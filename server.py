import os
import re
import random
import string
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def check_syntax(code):
    """Kiểm tra cú pháp LuaU nhanh"""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    
    in_string = False
    string_char = None
    escaping = False
    in_comment = False
    
    for i, char in enumerate(code):
        if escaping:
            escaping = False
            continue
            
        if in_comment:
            if char == '\n':
                in_comment = False
            continue
            
        if not in_string and not in_comment and i < len(code) - 1 and char == '-' and code[i+1] == '-':
            in_comment = True
            continue
            
        if in_string:
            if char == '\\':
                escaping = True
            elif char == string_char:
                in_string = False
            continue
            
        if char in ('"', "'"):
            in_string = True
            string_char = char
            continue
            
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                return False, "Unmatched closing bracket"
            if brackets[stack.pop()] != char:
                return False, "Mismatched brackets"
                
    if stack:
        return False, "Unclosed bracket"
    if in_string:
        return False, "Unclosed string"
        
    return True, "Syntax OK"

def obfuscate(code):
    """Obfuscation mạnh nhưng nhẹ nhàng"""
    
    # 1. Mã hóa strings với XOR - phương pháp nhẹ nhất
    def encrypt_string(s):
        key = random.randint(1, 255)
        # Mã hóa XOR + Base64
        encrypted = ''.join(chr(ord(c) ^ key) for c in s)
        b64 = base64.b64encode(encrypted.encode()).decode()
        
        # Decoder ngắn gọn
        return f"(loadstring((function(s,k)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=b:find(s:sub(i,i))-1 if v>=0 then r=r..string.char(v)end end local x=''for j=1,#r do x=x..string.char(bit32.bxor(r:byte(j),k))end return x end)('{b64}',{key})))()"
    
    # Chỉ mã hóa strings dài > 5 ký tự để giảm dung lượng
    def should_encrypt(s):
        return len(s) > 5 and not s.strip().startswith('http')
    
    code = re.sub(r'"(.*?)"', lambda m: encrypt_string(m.group(1)) if should_encrypt(m.group(1)) else f'"{m.group(1)}"', code)
    code = re.sub(r"'(.*?)'", lambda m: encrypt_string(m.group(1)) if should_encrypt(m.group(1)) else f"'{m.group(1)}'", code)
    
    # 2. Đổi tên biến tối ưu - chỉ đổi biến dài
    vars = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    # Chỉ đổi tên biến dài > 3 ký tự
    long_vars = [v for v in vars - keywords if len(v) > 3]
    
    for var in long_vars:
        new_name = '_' + ''.join(random.choices('abcdef0123456789', k=6))
        code = re.sub(r'\b' + re.escape(var) + r'\b', new_name, code)
    
    # 3. Thêm junk code tối thiểu nhưng hiệu quả
    junk_lines = [
        'if math.random()>999 then end',
        'for _=1,0 do break end'
    ]
    
    # Chỉ thêm junk code ở một số vị trí
    lines = code.split('\n')
    if len(lines) > 10:
        insert_points = random.sample(range(5, len(lines)-5), min(3, len(lines)//10))
        for point in sorted(insert_points, reverse=True):
            if point < len(lines):
                lines.insert(point, random.choice(junk_lines))
    
    code = '\n'.join(lines)
    
    # 4. Mã hóa toàn bộ code với XOR + Base64
    key = random.randint(1, 255)
    encrypted = ''.join(chr(ord(c) ^ key) for c in code)
    b64_code = base64.b64encode(encrypted.encode()).decode()
    
    # 5. Tạo output cực ngắn gọn
    decoder = f'''local k={key}local s='{b64_code}'local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=b:find(s:sub(i,i))-1 if v>=0 then r=r..string.char(v)end end local x=''for j=1,#r do x=x..string.char(bit32.bxor(r:byte(j),k))end loadstring(x)()'''
    
    return decoder

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'Lỗi đọc file'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập code'}), 400

    is_valid, message = check_syntax(input_code)
    if not is_valid:
        return jsonify({'error': f'Lỗi cú pháp: {message}'}), 400

    try:
        obfuscated = obfuscate(input_code)
        return jsonify({
            'output': obfuscated,
            'status': 'Mã hóa thành công!'
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500

@app.route('/api/check_syntax', methods=['POST'])
def api_check_syntax():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'Lỗi đọc file'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập code'}), 400

    is_valid, message = check_syntax(input_code)
    return jsonify({'valid': is_valid, 'message': message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
