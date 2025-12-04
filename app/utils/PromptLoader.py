import os
from pathlib import Path


class PromptLoader:
    """Utility to load prompt templates from files."""
    
    def __init__(self, prompts_dir: str | None = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files (defaults to docs/prompts/)
        """
        if prompts_dir is None:
            # Default to docs/prompts/ relative to project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            prompts_dir = str(project_root / "docs" / "prompts")
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}
    
    def load(self, template_name: str) -> str:
        """
        Load a prompt template from file.
        
        Args:
            template_name: Name of the template file (without path, e.g., 'master.prompt.txt')
            
        Returns:
            The prompt template content
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
        """
        if template_name in self._cache:
            return self._cache[template_name]
        
        template_path = self.prompts_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._cache[template_name] = content
        return content
    
    def format(self, template_name: str, **kwargs) -> str:
        """
        Load and format a prompt template with variables.
        
        Args:
            template_name: Name of the template file
            **kwargs: Variables to substitute in the template
            
        Returns:
            The formatted prompt
        """
        template = self.load(template_name)
        return template.format(**kwargs)
