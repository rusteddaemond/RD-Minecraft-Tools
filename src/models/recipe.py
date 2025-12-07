"""Models for recipe operations."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class RecipeResult:
    """Result extracted from a recipe JSON.
    
    Represents the output(s) of a Minecraft recipe.
    """
    recipe_id: str
    namespace: str
    results: List[str]
    
    def to_namespace_objects(self) -> List[str]:
        """Convert results to namespace:object format.
        
        Returns:
            List of strings in format "namespace:object_id"
        """
        formatted_results = []
        for result in self.results:
            if ":" in result:
                formatted_results.append(result)
            else:
                formatted_results.append(f"{self.namespace}:{result}")
        return formatted_results
