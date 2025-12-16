import os
import ast
import re
from pathlib import Path

ROOT = Path(r"C:\garam\garam")

# 의심스러운 패턴들: markdown/AI 잔해 가능성
SUSPICIOUS_PATTERNS = [
    r"```",              # 코드 블록 마크다운
    r"^python\)?$",      # 단독 'python' or 'python)' 라인
    r"^```python",       # ```python
    r"^#+\s",            # markdown heading (# ### 등)
    r"\[GARAM\]",        # 배치 출력이 코드에 섞인 경우
]

def check_python_file(path: Path):
    rel = path.relative_to(ROOT)
    issues = []

    text = path.read_text(encoding="utf-8", errors="ignore")

    # 1) AST 파싱으로 문법 오류 체크
    try:
        ast.parse(text, filename=str(rel))
    except SyntaxError as e:
        issues.append(f"SYNTAX_ERROR: {e.msg} (line {e.lineno}, col {e.offset})")

    # 2) 의심 패턴 스캔
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for pat in SUSPICIOUS_PATTERNS:
            if re.search(pat, line):
                issues.append(f"SUSPICIOUS_PATTERN '{pat}' at line {i}: {line.strip()}")
                break

    # 3) 중복 함수 이름 대략 체크 (완벽하진 않지만 힌트용)
    func_names = {}
    try:
        tree = ast.parse(text, filename=str(rel))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_names.setdefault(node.name, 0)
                func_names[node.name] += 1
        for name, cnt in func_names.items():
            if cnt >= 2:
                issues.append(f"DUPLICATE_FUNCTION_DEF: '{name}' appears {cnt} times")
    except SyntaxError:
        # 문법 에러가 있으면 위에서 이미 잡았으니 무시
        pass

    return issues


def main():
    print(f"[SCAN] Root: {ROOT}")

    total_files = 0
    problem_files = 0

    for path in ROOT.rglob("*.py"):
        # 가급적 가상환경/캐시 등은 제외
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in path.parts):
            continue

        total_files += 1
        issues = check_python_file(path)
        if issues:
            problem_files += 1
            print("=" * 80)
            print(f"[FILE] {path.relative_to(ROOT)}")
            for msg in issues:
                print(f"  - {msg}")

    print("=" * 80)
    print(f"[RESULT] scanned: {total_files} python files, suspicious/problematic: {problem_files}")


if __name__ == "__main__":
    main()
