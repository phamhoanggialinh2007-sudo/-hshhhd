import os
import re
import random
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def check_syntax(code):
    """Kiểm tra cú pháp LuaU"""
    stack = []
    brackets = {'(': ')', '[': ']', '{': '}'}
    
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
            
        if not in_string and i < len(code) - 1 and char == '-' and code[i+1] == '-':
            in_comment = True
            i += 1
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
    """Obfuscation đa phương pháp với junk code và flow control"""
    
    # 1. Đổi tên biến
    variables = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    var_map = {}
    for var in variables - keywords:
        if len(var) > 3:  # Chỉ đổi tên biến dài
            new_name = '_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
            var_map[var] = new_name
            code = code.replace(var, new_name)
    
    # 2. Mã hóa strings với nhiều phương pháp
    def encrypt_string(s):
        method = random.choice(['base64', 'ascii', 'reverse', 'xor'])
        
        if method == 'base64':
            b64 = base64.b64encode(s.encode()).decode()
            return f"(function() local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/' local r='' for i=1,#'{b64}' do local v=b:find('{b64}':sub(i,i))-1 if v>=0 then r=r..string.char(v) end end return r end)()"
        
        elif method == 'ascii':
            ascii_codes = [str(ord(c)) for c in s]
            return f"(function() local r='' for _,v in ipairs({{{','.join(ascii_codes)}}}) do r=r..string.char(v) end return r end)()"
        
        elif method == 'reverse':
            return f"'{s[::-1]}':reverse()"
        
        else:  # xor
            key = random.randint(1, 255)
            encoded = ''.join(chr(ord(c) ^ key) for c in s)
            return f"(function(s,k) local r='' for i=1,#s do r=r..string.char(s:byte(i)~k) end return r end)('{encoded}',{key})"
    
    # Mã hóa các strings dài
    strings = re.findall(r'"(.*?)"', code) + re.findall(r"'(.*?)'", code)
    for s in strings:
        if len(s) > 5 and not s.startswith('http'):
            encrypted = encrypt_string(s)
            code = code.replace(f'"{s}"', encrypted).replace(f"'{s}'", encrypted)
    
    # 3. Thêm junk code và flow obfuscation
    junk_functions = [
        'local function _junk() return math.random(100) end',
        'local _ = function() return nil end',
        'if false then while true do end end',
        'repeat until true',
        'for i=1,0 do break end',
        '::__label__:: goto __label__'
    ]
    
    flow_patterns = [
        'if math.random() > 0.5 then else end',
        'local _cond = true; if _cond then else end',
        'while false do break end'
    ]
    
    # Thêm junk functions
    code = random.choice(junk_functions) + '\n' + code
    
    # Thêm flow obfuscation
    lines = code.split('\n')
    for i in range(len(lines)):
        if random.random() < 0.1 and 'function' not in lines[i] and 'end' not in lines[i]:
            lines[i] = random.choice(flow_patterns) + '\n' + lines[i]
    
    code = '\n'.join(lines)
    
    # 4. Mã hóa toàn bộ code với Base64
    b64_code = base64.b64encode(code.encode()).decode()
    
    # 5. Tạo decoder với junk code
    decoder = f'''--[[ Obfuscated Code ]]
local function _decrypt()
    local _junk = function() return math.random(100) end
    _junk()
    
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    local s = '{b64_code}'
    local r = ''
    
    for i = 1, #s do
        local v = b:find(s:sub(i, i)) - 1
        if v >= 0 then
            r = r .. string.char(v)
        end
    end
    
    if math.random() > 2 then
        while true do end
    end
    
    return r
end

local code = _decrypt()
loadstring(code)()'''
    
    return decoder

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
        <head><title>Lua Obfuscator</title></head>
        <body>
            <h2>Lua Code Obfuscator</h2>
            <form action="/api/obfuscate" method="post">
                <textarea name="code" rows="15" cols="80" placeholder="Paste your Lua code here"></textarea>
                <br>
                <input type="submit" value="Obfuscate">
            </form>
        </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
