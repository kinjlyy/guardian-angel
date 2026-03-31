import re

with open(r"c:\Users\kinjal\guardian-angel\ui\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the content inside f""" ... """
match = re.search(r'f"""(.*?)"""', content, re.DOTALL)
if match:
    f_string_content = match.group(1)
    
    # Count occurrences of single { and } (not including {{ and }})
    # Actually, f-strings care about the total number of { and } when considering parity.
    # Every single { must be a {{. Every single } must be a }}.
    # UNLESS it's a variable like {BACKEND}.
    
    # Let's just find any instance of { or } that is NOT part of a pair {{ or }} 
    # and NOT inside a variable {VAR}.
    
    print(f"Total length: {len(f_string_content)}")
    
    # Scan characters
    opens = []
    closes = []
    i = 0
    while i < len(f_string_content):
        if f_string_content[i] == '{':
            if i + 1 < len(f_string_content) and f_string_content[i+1] == '{':
                i += 2
                continue
            opens.append(i)
        elif f_string_content[i] == '}':
            if i + 1 < len(f_string_content) and f_string_content[i+1] == '}':
                i += 2
                continue
            closes.append(i)
        i += 1
        
    print(f"Single '{'{'}' count: {len(opens)}")
    print(f"Single '{'}'}' count: {len(closes)}")
    
    if len(opens) != len(closes):
        print("IMBALANCE DETECTED!")
    
    print("\nPositions of single opens:")
    for p in opens:
        # Get line number
        line_no = f_string_content[:p].count('\n') + 11 # Offset for file start
        context = f_string_content[max(0, p-20):min(len(f_string_content), p+20)].replace('\n', ' ')
        print(f"Line {line_no}: ...{context}...")
        
    print("\nPositions of single closes:")
    for p in closes:
        line_no = f_string_content[:p].count('\n') + 11
        context = f_string_content[max(0, p-20):min(len(f_string_content), p+20)].replace('\n', ' ')
        print(f"Line {line_no}: ...{context}...")

else:
    print("F-string not found")
