import os
import re
import random
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def check_syntax(code):
    """Kiểm tra cú pháp LuaU đơn giản"""
    # Kiểm tra các bracket cân bằng
    stack = []
    brackets = {'(': ')', '[': ']', '{': '}'}
    
    in_string = False
    string_char = None
    escaping = False
    
    i = 0
    while i < len(code):
        char = code[i]
        
        if escaping:
            escaping = False
            i += 1
            continue
            
        if in_string:
            if char == '\\':
                escaping = True
            elif char == string_char:
                in_string = False
            i += 1
            continue
            
        if char in ('"', "'"):
            in_string = True
            string_char = char
            i += 1
            continue
            
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                return False, "Unmatched closing bracket"
            if brackets[stack.pop()] != char:
                return False, "Mismatched brackets"
        
        i += 1
                
    if stack:
        return False, "Unclosed bracket"
    if in_string:
        return False, "Unclosed string"
        
    return True, "Syntax OK"

def obfuscate(code):
    """Obfuscation nhẹ nhàng nhưng hiệu quả"""
    
    # 1. Đổi tên biến đơn giản
    variables = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    # Chỉ đổi tên các biến dài
    long_vars = [v for v in variables - keywords if len(v) > 4]
    var_map = {}
    
    for var in long_vars:
        new_name = 'v' + str(random.randint(1000, 9999))
        var_map[var] = new_name
        code = code.replace(var, new_name)
    
    # 2. Mã hóa string đơn giản (chỉ strings dài)
    def simple_encrypt(s):
        if len(s) < 8:  # Chỉ mã hóa string dài
            return f'"{s}"'
        
        key = random.randint(1, 255)
        # Mã hóa XOR đơn giản
        encrypted = ''.join(chr(ord(c) ^ key) for c in s)
        b64 = base64.b64encode(encrypted.encode()).decode()
        
        return f'((function(s,k)return loadstring(string.char(({key})))(s,k)end)(\'{b64}\',{key}))'
    
    # Tìm và mã hóa các string
    strings = re.findall(r'"(.*?)"', code)
    for s in strings:
        if len(s) >= 8:
            encrypted = simple_encrypt(s)
            code = code.replace(f'"{s}"', encrypted, 1)
    
    # 3. Thêm một ít junk code
    junk_codes = [
        'if nil then end',
        'local _=1',
        'do end'
    ]
    
    lines = code.split('\n')
    if len(lines) > 20:
        # Thêm junk code ở một vài vị trí
        insert_positions = random.sample(range(5, len(lines)-5), min(2, len(lines)//20))
        for pos in sorted(insert_positions, reverse=True):
            lines.insert(pos, random.choice(junk_codes))
    
    code = '\n'.join(lines)
    
    # 4. Mã hóa toàn bộ code đơn giản
    # Chỉ mã hóa nếu code đủ dài
    if len(code) > 100:
        key = random.randint(1, 255)
        encrypted = ''.join(chr(ord(c) ^ key) for c in code)
        b64_code = base64.b64encode(encrypted.encode()).decode()
        
        # Decoder đơn giản
        decoder = f'''local k={key}local s=[[{b64_code}]]local r=""for i=1,#s do r=r..string.char(string.byte(s,i)~k)end loadstring(r)()'''
        return decoder
    
    return code

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'Cannot read file'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Please provide Lua code'}), 400

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
        return jsonify({'error': f'Obfuscation failed: {str(e)}'}), 500

@app.route('/api/check_syntax', methods=['POST'])
def api_check_syntax():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except:
            return jsonify({'error': 'Cannot read file'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Please provide Lua code'}), 400

    is_valid, message = check_syntax(input_code)
    return jsonify({'valid': is_valid, 'message': message})

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h2>Lua Code Obfuscator</h2>
            <form action="/api/obfuscate" method="post">
                <textarea name="code" rows="10" cols="50" placeholder="Paste Lua code here"></textarea>
                <br>
                <input type="submit" value="Obfuscate">
            </form>
        </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
