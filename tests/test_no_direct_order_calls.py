"""
Execution Authority Guard
Statically analyzes the codebase to ensure that ONLY authorized modules (e.g., ExecutionBroker)
are calling critical order execution methods (send_order, place_order).
"""

import unittest
import os
import ast
from pathlib import Path

# Authorized modules that are allowed to send orders
AUTHORIZED_MODULES = [
    'execution_broker.py',
    'kiwoom_broker.py',
    'real_broker_sim.py',
    'paper_broker.py',
    'test_no_direct_order_calls.py', # Self
    'mock_broker.py' # For testing
]

# Critical methods that should be restricted
CRITICAL_METHODS = [
    'send_order',
    'SendOrder', # Kiwoom API
    'place_order'
]

class TestExecutionAuthority(unittest.TestCase):
    
    def test_no_unauthorized_orders(self):
        """Scan all python files for unauthorized order calls"""
        project_root = Path(__file__).parent.parent.parent
        
        violations = []
        
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if not file.endswith('.py'): continue
                
                # Skip tests and venv
                if 'tests' in root or 'venv' in root or '.git' in root: continue
                
                file_path = Path(root) / file
                
                # Check if authorized
                if file in AUTHORIZED_MODULES: continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Attribute):
                                method_name = node.func.attr
                                if method_name in CRITICAL_METHODS:
                                    violations.append(f"{file}: Line {node.lineno} calls '{method_name}'")
                            elif isinstance(node.func, ast.Name):
                                method_name = node.func.id
                                if method_name in CRITICAL_METHODS:
                                    violations.append(f"{file}: Line {node.lineno} calls '{method_name}'")
                                    
                except Exception as e:
                    # Skip files that can't be parsed (encoding issues etc)
                    pass
                    
        if violations:
            print("\n❌ UNAUTHORIZED ORDER CALLS DETECTED:")
            for v in violations:
                print(f"   - {v}")
            self.fail(f"Found {len(violations)} unauthorized order calls! See output.")
        else:
            print("\n✅ No unauthorized order calls found.")

if __name__ == "__main__":
    unittest.main()
