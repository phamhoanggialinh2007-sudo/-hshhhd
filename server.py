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
    
    for char in code:
        if escaping:
            escaping = False
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
    """Obfuscation mạnh nhưng ngắn gọn"""
    # 1. Mã hóa strings với XOR
    def encrypt_string(s):
        key = random.randint(1, 255)
        encrypted = ''.join(chr(ord(c) ^ key) for c in s)
        b64 = base64.b64encode(encrypted.encode()).decode()
        return f"(function(s,k)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end local d=''for j=1,#r do d=d..string.char(bit32.bxor(r:byte(j),k))end return d end)('{b64}',{key})"
    
    # Mã hóa tất cả strings
    code = re.sub(r'"(.*?)"', lambda m: encrypt_string(m.group(1)), code)
    code = re.sub(r"'(.*?)'", lambda m: encrypt_string(m.group(1)), code)
    
    # 2. Đổi tên biến ngắn gọn
    vars = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    for var in vars - keywords:
        new_name = '_' + ''.join(random.choices('abcdef0123456789', k=8))
        code = re.sub(r'\b' + re.escape(var) + r'\b', new_name, code)
    
    # 3. Thêm junk code ngắn
    junk_lines = [
        'if math.random()>999 then end',
        'for _=1,1 do break end',
        'do end',
        '::a::goto a'
    ]
    
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if random.random() < 0.2 and line.strip():
            new_lines.append(random.choice(junk_lines))
    
    code = '\n'.join(new_lines)
    
    # 4. Mã hóa toàn bộ code thành long string
    key = random.randint(1, 255)
    encrypted = ''.join(chr(ord(c) ^ key) for c in code)
    b64_code = base64.b64encode(encrypted.encode()).decode()
    
    # 5. Tạo output dạng long string ngắn gọn
    decoder = f'''local function d(s,k)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end local x=''for j=1,#r do x=x..string.char(bit32.bxor(r:byte(j),k))end return x end loadstring(d('{b64_code}',{key}))()'''
    
    return f"--[[Obfuscated]]{decoder}"

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
