"""
Tree-sitter parser for Python code analysis.
Extracts AST structure, functions, classes, and code blocks.
"""

import tree_sitter_python
from tree_sitter import Language, Parser
from dataclasses import dataclass
from typing import Literal, Optional
import structlog

logger = structlog.get_logger()

@dataclass
class CodeBlock:
    """Represents a structured block of code extracted from AST."""
    type: str  # function_definition, class_definition, etc.
    name: Optional[str]
    start_line: int
    end_line: int
    content: str
    complexity: int = 1

class TreeSitterParser:
    """
    Parser for extracting code structure using tree-sitter.
    Currently supports Python.
    """
    
    def __init__(self):
        try:
            self.PY_LANGUAGE = Language(tree_sitter_python.language())
            self.parser = Parser(self.PY_LANGUAGE)
        except Exception as e:
            logger.error("tree_sitter_init_failed", error=str(e))
            self.parser = None

    def parse_code(self, code: str, filename: str) -> list[CodeBlock]:
        """
        Parse code and extract top-level blocks.
        
        Args:
            code: Source code string
            filename: Name of file (for logging/context)
            
        Returns:
            List of CodeBlock objects
        """
        if not self.parser or not code.strip():
            return []
            
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            blocks = []
            
            cursor = tree.walk()
            
            # Simple recursive traversal to find functions and classes
            # In a real implementation, we'd use a query or smarter traversal
            self._traverse_tree(cursor.node, code, blocks)
            
            logger.info("tree_sitter_parse_success", filename=filename, blocks=len(blocks))
            return blocks[:20]  # Limit findings per file
            
        except Exception as e:
            logger.error("tree_sitter_parse_error", filename=filename, error=str(e))
            return []

    def _traverse_tree(self, node, code, blocks):
        """Recursively find relevant nodes."""
        if node.type in ["function_definition", "class_definition"]:
            name = None
            # Find identifier child
            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf8")
                    break
            
            # Extract content
            lines = code.splitlines()
            start = node.start_point[0]
            end = node.end_point[0]
            content = "\n".join(lines[start:end+1])
            
            blocks.append(CodeBlock(
                type=node.type,
                name=name,
                start_line=start + 1,  # 1-indexed
                end_line=end + 1,
                content=content
            ))
            
        for child in node.children:
            self._traverse_tree(child, code, blocks)

    def get_function_blocks(self, code: str) -> list[CodeBlock]:
        """Convenience method to get only function blocks."""
        blocks = self.parse_code(code, "memory")
        return [b for b in blocks if b.type == "function_definition"]
