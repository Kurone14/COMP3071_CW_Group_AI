"""
Obstacle classifier for determining obstacle types in the warehouse environment.
Uses machine learning techniques to classify obstacles based on robot interactions.
"""

from typing import Dict, Tuple, List, Optional, Any
import random
from enum import Enum

from core.models.grid import Grid, CellType
from core.utils.logger import get_component_logger


class ObstacleFeature(Enum):
    """Features used for obstacle classification"""
    INTERACTION_SUCCESS_RATE = "success_rate"
    OBSTACLE_AGE = "age"
    INTERACTION_COUNT = "interaction_count"
    LAST_INTERACTION_TIME = "last_interaction"
    ROBOT_WAIT_TIME = "wait_time"
    SPATIAL_CONSISTENCY = "spatial_consistency"


class ObstacleClassifier:
    """
    Classifies obstacles based on robot interactions and environmental factors.
    Uses a weighted feature approach to determine the most likely obstacle type.
    """
    
    def __init__(self, grid: Grid):
        """
        Initialize the obstacle classifier
        
        Args:
            grid: The grid environment
        """
        self.grid = grid
        self.logger = get_component_logger("ObstacleClassifier")
        
        # Classification thresholds
        self.confidence_threshold = 0.7
        self.reclassification_threshold = 0.3
        
        # Feature weights for classification
        self.feature_weights = {
            ObstacleFeature.INTERACTION_SUCCESS_RATE: 0.45,
            ObstacleFeature.OBSTACLE_AGE: 0.15,
            ObstacleFeature.INTERACTION_COUNT: 0.15,
            ObstacleFeature.LAST_INTERACTION_TIME: 0.10,
            ObstacleFeature.ROBOT_WAIT_TIME: 0.10,
            ObstacleFeature.SPATIAL_CONSISTENCY: 0.05
        }
        
        # Classification history
        self.classification_history: Dict[Tuple[int, int], List[Dict]] = {}
    
    def classify_obstacle(self, x: int, y: int, 
                         interaction_history: List[Dict], 
                         obstacle_metadata: Dict) -> Tuple[CellType, float]:
        """
        Classify an obstacle based on robot interactions and metadata
        
        Args:
            x, y: Obstacle coordinates
            interaction_history: History of robot interactions with this obstacle
            obstacle_metadata: Metadata about the obstacle (age, lifespan, etc.)
            
        Returns:
            Tuple[CellType, float]: Classified obstacle type and confidence level
        """
        # Extract features from interaction history and metadata
        features = self._extract_features(x, y, interaction_history, obstacle_metadata)
        
        # Calculate class probabilities
        probabilities = self._calculate_probabilities(features)
        
        # Get the most likely class
        obstacle_type, confidence = self._get_most_likely_class(probabilities)
        
        # Store classification in history
        self._update_classification_history(x, y, obstacle_type, confidence, features)
        
        return obstacle_type, confidence
    
    def _extract_features(self, x: int, y: int, 
                        interaction_history: List[Dict], 
                        obstacle_metadata: Dict) -> Dict[ObstacleFeature, float]:
        """
        Extract features from interaction history and metadata
        
        Args:
            x, y: Obstacle coordinates
            interaction_history: History of robot interactions with this obstacle
            obstacle_metadata: Metadata about the obstacle
            
        Returns:
            Dict[ObstacleFeature, float]: Dictionary of features and their values
        """
        features = {}
        
        # Calculate success rate from interaction history
        if interaction_history:
            success_count = sum(1 for interaction in interaction_history if interaction.get('success', False))
            features[ObstacleFeature.INTERACTION_SUCCESS_RATE] = success_count / len(interaction_history)
            features[ObstacleFeature.INTERACTION_COUNT] = min(1.0, len(interaction_history) / 10.0)  # Normalize
            
            # Last interaction time (normalized, 0=recent, 1=old)
            last_times = [interaction.get('timestamp', 0) for interaction in interaction_history]
            if last_times:
                latest_time = max(last_times)
                current_time = obstacle_metadata.get('current_time', latest_time)
                time_diff = current_time - latest_time
                features[ObstacleFeature.LAST_INTERACTION_TIME] = min(1.0, time_diff / 20.0)  # Normalize
        else:
            features[ObstacleFeature.INTERACTION_SUCCESS_RATE] = 0.0
            features[ObstacleFeature.INTERACTION_COUNT] = 0.0
            features[ObstacleFeature.LAST_INTERACTION_TIME] = 1.0  # No recent interactions
        
        # Obstacle age (normalized, 0=new, 1=old)
        age = obstacle_metadata.get('age', 0)
        max_age = 50  # Maximum expected age
        features[ObstacleFeature.OBSTACLE_AGE] = min(1.0, age / max_age)
        
        # Robot wait time (normalized, 0=no wait, 1=long wait)
        wait_time = obstacle_metadata.get('wait_time', 0)
        max_wait = 10  # Maximum expected wait time
        features[ObstacleFeature.ROBOT_WAIT_TIME] = min(1.0, wait_time / max_wait)
        
        # Spatial consistency (nearby obstacles of same type) - simulate with random for now
        # In a real implementation, this would check nearby obstacles
        features[ObstacleFeature.SPATIAL_CONSISTENCY] = random.uniform(0.0, 1.0)
        
        return features
    
    def _calculate_probabilities(self, features: Dict[ObstacleFeature, float]) -> Dict[CellType, float]:
        """
        Calculate probabilities for each obstacle type
        
        Args:
            features: Dictionary of features and their values
            
        Returns:
            Dict[CellType, float]: Dictionary of obstacle types and their probabilities
        """
        # Initialize probabilities for each class
        probabilities = {
            CellType.PERMANENT_OBSTACLE: 0.0,
            CellType.SEMI_PERMANENT_OBSTACLE: 0.0,
            CellType.TEMPORARY_OBSTACLE: 0.0
        }
        
        # Calculate probability for permanent obstacles
        if ObstacleFeature.INTERACTION_SUCCESS_RATE in features:
            # Permanent obstacles have low success rate
            success_rate = features[ObstacleFeature.INTERACTION_SUCCESS_RATE]
            probabilities[CellType.PERMANENT_OBSTACLE] += (1.0 - success_rate) * self.feature_weights[ObstacleFeature.INTERACTION_SUCCESS_RATE]
            
            # Semi-permanent have medium success rate
            semi_perm_factor = 1.0 - abs(success_rate - 0.5) * 2.0  # Peaks at 0.5
            probabilities[CellType.SEMI_PERMANENT_OBSTACLE] += semi_perm_factor * self.feature_weights[ObstacleFeature.INTERACTION_SUCCESS_RATE]
            
            # Temporary obstacles have high success rate
            probabilities[CellType.TEMPORARY_OBSTACLE] += success_rate * self.feature_weights[ObstacleFeature.INTERACTION_SUCCESS_RATE]
        
        # Age influences obstacle type
        if ObstacleFeature.OBSTACLE_AGE in features:
            age_factor = features[ObstacleFeature.OBSTACLE_AGE]
            probabilities[CellType.PERMANENT_OBSTACLE] += age_factor * self.feature_weights[ObstacleFeature.OBSTACLE_AGE]
            probabilities[CellType.SEMI_PERMANENT_OBSTACLE] += (1.0 - abs(age_factor - 0.5) * 2.0) * self.feature_weights[ObstacleFeature.OBSTACLE_AGE]
            probabilities[CellType.TEMPORARY_OBSTACLE] += (1.0 - age_factor) * self.feature_weights[ObstacleFeature.OBSTACLE_AGE]
        
        # Interaction count influences reliability of classification
        if ObstacleFeature.INTERACTION_COUNT in features:
            interaction_factor = features[ObstacleFeature.INTERACTION_COUNT]
            # More interactions increase confidence in classification
            for obstacle_type in probabilities:
                probabilities[obstacle_type] += interaction_factor * probabilities[obstacle_type] * self.feature_weights[ObstacleFeature.INTERACTION_COUNT]
        
        # Recent interactions increase likelihood of accurate classification
        if ObstacleFeature.LAST_INTERACTION_TIME in features:
            recency_factor = 1.0 - features[ObstacleFeature.LAST_INTERACTION_TIME]
            for obstacle_type in probabilities:
                probabilities[obstacle_type] += recency_factor * probabilities[obstacle_type] * self.feature_weights[ObstacleFeature.LAST_INTERACTION_TIME]
        
        # Wait time influences obstacle type
        if ObstacleFeature.ROBOT_WAIT_TIME in features:
            wait_factor = features[ObstacleFeature.ROBOT_WAIT_TIME]
            # Long waits suggest temporary obstacles (robots waiting for them to disappear)
            probabilities[CellType.TEMPORARY_OBSTACLE] += wait_factor * self.feature_weights[ObstacleFeature.ROBOT_WAIT_TIME]
            # Medium waits suggest semi-permanent obstacles
            probabilities[CellType.SEMI_PERMANENT_OBSTACLE] += (1.0 - abs(wait_factor - 0.5) * 2.0) * self.feature_weights[ObstacleFeature.ROBOT_WAIT_TIME]
            # Short/no waits suggest permanent obstacles (robots don't wait for them)
            probabilities[CellType.PERMANENT_OBSTACLE] += (1.0 - wait_factor) * self.feature_weights[ObstacleFeature.ROBOT_WAIT_TIME]
        
        # Spatial consistency influences classification
        if ObstacleFeature.SPATIAL_CONSISTENCY in features:
            spatial_factor = features[ObstacleFeature.SPATIAL_CONSISTENCY]
            # Adjust all probabilities based on spatial consistency
            for obstacle_type in probabilities:
                probabilities[obstacle_type] += spatial_factor * probabilities[obstacle_type] * self.feature_weights[ObstacleFeature.SPATIAL_CONSISTENCY]
        
        # Normalize probabilities to sum to 1
        total_probability = sum(probabilities.values())
        if total_probability > 0:
            for obstacle_type in probabilities:
                probabilities[obstacle_type] /= total_probability
        
        return probabilities
    
    def _get_most_likely_class(self, probabilities: Dict[CellType, float]) -> Tuple[CellType, float]:
        """
        Get the most likely obstacle class and its confidence
        
        Args:
            probabilities: Dictionary of obstacle types and their probabilities
            
        Returns:
            Tuple[CellType, float]: Most likely obstacle type and confidence level
        """
        most_likely_class = max(probabilities, key=probabilities.get)
        confidence = probabilities[most_likely_class]
        
        return most_likely_class, confidence
    
    def _update_classification_history(self, x: int, y: int, 
                                     obstacle_type: CellType, 
                                     confidence: float,
                                     features: Dict[ObstacleFeature, float]) -> None:
        """
        Update classification history for this obstacle
        
        Args:
            x, y: Obstacle coordinates
            obstacle_type: Classified obstacle type
            confidence: Confidence in the classification
            features: Features used for classification
        """
        if (x, y) not in self.classification_history:
            self.classification_history[(x, y)] = []
        
        # Add this classification to history
        self.classification_history[(x, y)].append({
            'type': obstacle_type,
            'confidence': confidence,
            'features': {feature.value: value for feature, value in features.items()},
            'timestamp': random.randint(0, 100)  # Simulated timestamp for now
        })
        
        # Limit history size
        if len(self.classification_history[(x, y)]) > 10:
            self.classification_history[(x, y)] = self.classification_history[(x, y)][-10:]
    
    def should_reclassify(self, x: int, y: int, 
                        current_type: CellType, 
                        interaction_success: bool) -> bool:
        """
        Determine if an obstacle should be reclassified based on new interaction
        
        Args:
            x, y: Obstacle coordinates
            current_type: Current obstacle type
            interaction_success: Whether a robot successfully navigated past the obstacle
            
        Returns:
            bool: True if obstacle should be reclassified
        """
        # If permanent obstacle was successfully navigated, definitely reclassify
        if current_type == CellType.PERMANENT_OBSTACLE and interaction_success:
            return True
        
        # If history exists, check confidence trend
        if (x, y) in self.classification_history and self.classification_history[(x, y)]:
            # Get recent classifications
            recent_history = self.classification_history[(x, y)][-3:]
            
            # If recent classifications consistently disagree with current type
            disagreements = sum(1 for entry in recent_history 
                              if entry['type'] != current_type and 
                              entry['confidence'] > self.reclassification_threshold)
            
            if disagreements >= 2:  # At least 2 of 3 recent classifications disagree
                return True
            
            # If confidence in current type is decreasing
            if len(recent_history) >= 2:
                confidence_trend = [
                    entry['confidence'] for entry in recent_history 
                    if entry['type'] == current_type
                ]
                
                if confidence_trend and sum(confidence_trend) / len(confidence_trend) < self.reclassification_threshold:
                    return True
        
        # Default: don't reclassify
        return False
    
    def get_classification_confidence(self, x: int, y: int, obstacle_type: CellType) -> float:
        """
        Get the confidence in a particular classification for an obstacle
        
        Args:
            x, y: Obstacle coordinates
            obstacle_type: Obstacle type to check confidence for
            
        Returns:
            float: Confidence level (0.0-1.0)
        """
        if (x, y) not in self.classification_history or not self.classification_history[(x, y)]:
            return 0.0
        
        # Get recent classifications of this type
        recent_history = self.classification_history[(x, y)][-5:]
        relevant_entries = [entry for entry in recent_history if entry['type'] == obstacle_type]
        
        if not relevant_entries:
            return 0.0
        
        # Return average confidence
        return sum(entry['confidence'] for entry in relevant_entries) / len(relevant_entries)
    
    def suggest_lifespan(self, obstacle_type: CellType) -> int:
        """
        Suggest an appropriate lifespan for an obstacle type
        
        Args:
            obstacle_type: Type of obstacle
            
        Returns:
            int: Suggested lifespan in cycles (-1 for permanent)
        """
        if obstacle_type == CellType.PERMANENT_OBSTACLE:
            return -1
        elif obstacle_type == CellType.SEMI_PERMANENT_OBSTACLE:
            # Some randomness in semi-permanent lifespan
            return random.randint(25, 35)
        elif obstacle_type == CellType.TEMPORARY_OBSTACLE:
            # Some randomness in temporary lifespan
            return random.randint(8, 12)
        else:
            return 10  # Default lifespan