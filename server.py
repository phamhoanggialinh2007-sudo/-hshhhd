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
    """Kiểm tra cú pháp LuaU"""
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
    """Obfuscation đa lớp mã hóa"""
    # 1. Mã hóa strings với nhiều phương pháp
    def encrypt_string(s):
        method = random.choice(['xor', 'shift', 'reverse', 'base64'])
        
        if method == 'xor':
            key = random.randint(1, 255)
            encrypted = ''.join(chr(ord(c) ^ key) for c in s)
            b64 = base64.b64encode(encrypted.encode()).decode()
            return f"(function(s,k)local r=''for i=1,#s do r=r..string.char((string.byte(s,i)+k)%256)end return r end)((function(s)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end return r end)('{b64}'),{key})"
        
        elif method == 'shift':
            shift = random.randint(1, 25)
            encrypted = ''.join(chr((ord(c) + shift) % 256) for c in s)
            b64 = base64.b64encode(encrypted.encode()).decode()
            return f"(function(s,k)local r=''for i=1,#s do r=r..string.char((string.byte(s,i)-k)%256)end return r end)((function(s)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end return r end)('{b64}'),{shift})"
        
        elif method == 'reverse':
            encrypted = s[::-1]
            b64 = base64.b64encode(encrypted.encode()).decode()
            return f"(function(s)return s:reverse()end)((function(s)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end return r end)('{b64}'))"
        
        else:  # base64
            b64 = base64.b64encode(s.encode()).decode()
            return f"(function(s)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end return r end)('{b64}')"
    
    # Mã hóa strings
    code = re.sub(r'"(.*?)"', lambda m: encrypt_string(m.group(1)), code)
    code = re.sub(r"'(.*?)'", lambda m: encrypt_string(m.group(1)), code)
    
    # 2. Đổi tên biến với nhiều pattern
    vars = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    patterns = [
        lambda: '_' + ''.join(random.choices('abcdef0123456789', k=8)),
        lambda: '__' + ''.join(random.choices('ABCDEF0123456789', k=6)),
        lambda: 'v' + str(random.randint(10000, 99999)),
        lambda: ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=3)) + '_' + str(random.randint(100, 999))
    ]
    
    for var in vars - keywords:
        new_name = random.choice(patterns)()
        code = re.sub(r'\b' + re.escape(var) + r'\b', new_name, code)
    
    # 3. Thêm anti-tamper code
    anti_tamper = [
        'if type(_G)=="table" and _G.debug then error("Debug mode detected") end',
        'if math.random()>999 then while true do end end',
        'local _=os.clock() if os.clock()-_>0.1 then error("Execution timeout") end',
        'if getfenv and getfenv().debug then error("Debug environment") end'
    ]
    
    # 4. Mã hóa toàn bộ code với phương pháp ngẫu nhiên
    method = random.choice(['xor', 'shift', 'base64'])
    
    if method == 'xor':
        key = random.randint(1, 255)
        encrypted = ''.join(chr(ord(c) ^ key) for c in code)
        b64_code = base64.b64encode(encrypted.encode()).decode()
        decoder = f'''local function d(s,k)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end local x=''for j=1,#r do x=x..string.char(bit32.bxor(r:byte(j),k))end return x end {random.choice(anti_tamper)} loadstring(d('{b64_code}',{key}))()'''
    
    elif method == 'shift':
        shift = random.randint(1, 50)
        encrypted = ''.join(chr((ord(c) + shift) % 256) for c in code)
        b64_code = base64.b64encode(encrypted.encode()).decode()
        decoder = f'''local function d(s,k)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end local x=''for j=1,#r do x=x..string.char((r:byte(j)-k)%256)end return x end {random.choice(anti_tamper)} loadstring(d('{b64_code}',{shift}))()'''
    
    else:  # base64
        b64_code = base64.b64encode(code.encode()).decode()
        decoder = f'''local function d(s)local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'local r=''for i=1,#s do local v=(b:find(s:sub(i,i))or 0)-1 if v>=0 then r=r..string.char(v)end end return r end {random.choice(anti_tamper)} loadstring(d('{b64_code}'))()'''
    
    return f"--[[Secure Obfuscator]]{decoder}"

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'File read error'}), 400

    if not input_code.strip():
        return jsonify({'error': 'No code provided'}), 400

    is_valid, message = check_syntax(input_code)
    if not is_valid:
        return jsonify({'error': f'Syntax error: {message}'}), 400

    try:
        obfuscated = obfuscate(input_code)
        return jsonify({
            'output': obfuscated,
            'status': 'Obfuscation successful!'
        })
    except Exception as e:
        return jsonify({'error': f'Obfuscation error: {str(e)}'}), 500

@app.route('/api/check_syntax', methods=['POST'])
def api_check_syntax():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'File read error'}), 400

    if not input_code.strip():
        return jsonify({'error': 'No code provided'}), 400

    is_valid, message = check_syntax(input_code)
    return jsonify({'valid': is_valid, 'message': message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
