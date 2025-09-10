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
    """Kiểm tra cú pháp LuaU với độ chính xác cao"""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    keyword_stack = []
    open_keywords = {'if', 'for', 'while', 'function', 'repeat'}
    close_map = {'if': 'end', 'for': 'end', 'while': 'end', 'function': 'end', 'repeat': 'until'}

    in_string = False
    string_type = None
    in_longstring = False
    in_line_comment = False
    escape_next = False

    lines = code.split('\n')
    for line_num, line in enumerate(lines):
        i = 0
        in_line_comment = False
        escape_next = False
        
        while i < len(line):
            c = line[i]

            # Xử lý escape sequences trong string
            if in_string and escape_next:
                escape_next = False
                i += 1
                continue

            # Xử lý comments
            if not in_string and not in_longstring and not in_line_comment:
                if line[i:i+4] == '--[[':
                    in_longstring = True
                    i += 4
                    continue
                elif line[i:i+2] == '--':
                    in_line_comment = True
                    i += 2
                    continue
                elif line[i:i+2] == '[[':
                    in_longstring = True
                    i += 2
                    continue

            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # Xử lý string
            if not in_string and not in_longstring and not in_line_comment and c in ('"', "'"):
                in_string = True
                string_type = c
                i += 1
                continue
            
            if in_string:
                if c == '\\':
                    escape_next = True
                elif c == string_type and not escape_next:
                    in_string = False
                i += 1
                continue

            # Kiểm tra brackets nếu không trong string/comment
            if not in_string and not in_longstring and not in_line_comment:
                if c in brackets:
                    stack.append((c, line_num))
                elif c in brackets.values():
                    if not stack:
                        return False, f"Unmatched closing bracket '{c}' at line {line_num+1}"
                    last_open, open_line = stack.pop()
                    if brackets[last_open] != c:
                        return False, f"Mismatched brackets: '{last_open}' at line {open_line+1} and '{c}' at line {line_num+1}"

            # Kiểm tra keywords
            if not in_string and not in_longstring and not in_line_comment and c.isalpha():
                token = ''
                start_pos = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    token += line[i]
                    i += 1
                
                # Kiểm tra xem token có phải là keyword không
                if token in open_keywords:
                    keyword_stack.append((token, line_num, start_pos))
                elif token in ('end', 'until'):
                    if not keyword_stack:
                        return False, f"Unmatched '{token}' at line {line_num+1}"
                    last_keyword, keyword_line, keyword_pos = keyword_stack[-1]
                    expected = close_map.get(last_keyword)
                    if token != expected:
                        return False, f"Mismatched block: '{last_keyword}' at line {keyword_line+1} and '{token}' at line {line_num+1}"
                    keyword_stack.pop()
                continue
            
            i += 1

    # Kiểm tra các lỗi còn lại
    if stack:
        last_bracket, line_num = stack[-1]
        return False, f"Unclosed bracket '{last_bracket}' at line {line_num+1}"
    
    if keyword_stack:
        last_keyword, line_num, pos = keyword_stack[-1]
        return False, f"Unclosed block '{last_keyword}' at line {line_num+1}"
    
    if in_string:
        return False, "Unclosed string literal"
    
    if in_longstring:
        return False, "Unclosed long string or comment"
    
    return True, "Syntax is valid"

def obfuscate(code):
    """Obfuscation LuaU cực mạnh - Level Moonsec Premium"""
    # Bước 1: Mã hóa string nhiều lớp
    def multi_layer_string_encrypt(s):
        # 3 lớp mã hóa XOR với keys khác nhau
        keys = [random.randint(1, 255) for _ in range(3)]
        encrypted = s
        
        # Mã hóa 3 lớp
        for key in keys:
            encrypted = ''.join(chr(ord(c) ^ key) for c in encrypted)
        
        # Base64 encode
        b64_encoded = base64.b64encode(encrypted.encode()).decode()
        
        # Tạo decoder phức tạp
        decoder_func = f'''function(str, k1, k2, k3)
    local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    local data=str:gsub('[^'..b..'=]', '')
    local result = ""
    local buffer = 0
    local bits = 0
    
    for i = 1, #data do
        if data:sub(i, i) == "=" then break end
        buffer = buffer * 64 + (b:find(data:sub(i, i)) - 1)
        bits = bits + 6
        if bits >= 8 then
            bits = bits - 8
            result = result .. string.char(bit32.band(bit32.rshift(buffer, bits), 0xFF))
            buffer = bit32.band(buffer, bit32.lshift(1, bits) - 1)
        end
    end
    
    -- Giải mã 3 lớp XOR
    for _, key in ipairs({{k3, k2, k1}}) do
        local temp = ""
        for j = 1, #result do
            temp = temp .. string.char(bit32.bxor(result:byte(j), key))
        end
        result = temp
    end
    
    return result
end'''
        
        return f"({decoder_func})('{b64_encoded}', {keys[0]}, {keys[1]}, {keys[2]})"
    
    # Mã hóa tất cả string
    def encrypt_strings(match):
        content = match.group(1)
        return multi_layer_string_encrypt(content)
    
    code = re.sub(r'"(.*?)"', encrypt_strings, code)
    code = re.sub(r"'(.*?)'", encrypt_strings, code)
    
    # Bước 2: Đổi tên biến cực mạnh
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    # Tìm tất cả identifiers
    identifiers = set()
    lines = code.split('\n')
    for line in lines:
        if '--' in line:
            line = line.split('--')[0]  # Bỏ comment
        matches = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', line)
        for match in matches:
            if match not in keywords and len(match) > 1:
                identifiers.add(match)
    
    # Tạo mapping name ngẫu nhiên
    obfuscated_names = {}
    for identifier in identifiers:
        # Tạo tên obfuscated với format phức tạp
        prefix = random.choice(['_', '__', '___'])
        random_chars = ''.join(random.choices('abcdef0123456789', k=12))
        obfuscated_names[identifier] = f"{prefix}{random_chars}"
    
    # Đổi tên biến (cẩn thận để không đổi trong string)
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 0:  # Không phải string
            for old_name, new_name in obfuscated_names.items():
                # Sử dụng word boundaries để tránh đổi nhầm
                tokens[i] = re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, tokens[i])
    
    code = ''.join(tokens)
    
    # Bước 3: Thêm junk code tinh vi
    junk_functions = []
    for i in range(15):  # Tạo 15 hàm junk
        func_name = f"_junk_func_{random.randint(10000, 99999)}"
        junk_code = f'''local function {func_name}()
    local _vars = {{}}
    for i = 1, math.random(3, 8) do
        table.insert(_vars, math.random(1000))
    end
    if math.random() > 0.5 then
        return table.concat(_vars, ",")
    else
        return #_vars
    end
end
{func_name}()'''
        junk_functions.append(junk_code)
    
    # Chèn junk functions vào đầu code
    code = '\n'.join(junk_functions) + '\n' + code
    
    # Bước 4: Thêm control flow obfuscation
    lines = code.split('\n')
    obfuscated_lines = []
    
    # Thêm junk code ngẫu nhiên
    junk_patterns = [
        'if math.random() > 0.999 then local _ = os.clock() end',
        'for _ = 1, math.random(1, 2) do break end',
        'repeat until math.random() > 0.5',
        'do local _ = function() return math.random() end end',
        'while false do print("Never executed") end',
        'local _t = {unpack({1,2,3})}',
        'if false then elseif false then else end'
    ]
    
    for line in lines:
        obfuscated_lines.append(line)
        # 30% chance thêm junk code sau mỗi dòng
        if random.random() < 0.3 and line.strip() and not line.strip().startswith('--'):
            obfuscated_lines.append(random.choice(junk_patterns))
    
    code = '\n'.join(obfuscated_lines)
    
    # Bước 5: Mã hóa toàn bộ code với nhiều lớp
    # Lớp 1: XOR encryption
    key1 = random.randint(1, 255)
    encrypted_code = ''.join(chr(ord(c) ^ key1) for c in code)
    
    # Lớp 2: Base64
    b64_encoded = base64.b64encode(encrypted_code.encode()).decode()
    
    # Bước 6: Tạo decoder phức tạp dạng long string
    decoder = f'''--[[ Obfuscated with Premium LuaU Obfuscator ]]
local function _decrypt_data(encrypted, key)
    -- Base64 decode
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    local result = ""
    local buffer = 0
    local bits = 0
    
    for i = 1, #encrypted do
        if encrypted:sub(i, i) == "=" then break end
        buffer = buffer * 64 + (b:find(encrypted:sub(i, i)) - 1)
        bits = bits + 6
        if bits >= 8 then
            bits = bits - 8
            result = result .. string.char(bit32.band(bit32.rshift(buffer, bits), 0xFF))
            buffer = bit32.band(buffer, bit32.lshift(1, bits) - 1)
        end
    end
    
    -- XOR decrypt
    local decrypted = ""
    for j = 1, #result do
        decrypted = decrypted .. string.char(bit32.bxor(result:byte(j), key))
    end
    
    return decrypted
end

-- Junk code anti-tamper
local _anti_tamper = function()
    local _env = getfenv and getfenv() or _G
    if _env.debug or _env.debugger then
        error("Execution in debug environment detected")
    end
end
_anti_tamper()

-- Decrypt and execute
local _encrypted_data = "{b64_encoded}"
local _decryption_key = {key1}
local _decrypted_code = _decrypt_data(_encrypted_data, _decryption_key)

-- Thêm junk code trước execution
for i = 1, math.random(2, 5) do
    local _ = math.random(1000)
    if _ > 999 then
        local __ = function() return _ end
    end
end

loadstring(_decrypted_code)()'''
    
    # Bước 7: Chuyển thành dạng long string một dòng
    # Thay thế các ký tự đặc biệt để tránh lỗi
    decoder = decoder.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    # Tạo final output dạng long string
    final_output = f'--[[ Premium Obfuscator v1.0 ]] return(function(...)local S={{"{decoder}"}} loadstring(S[1])() end)()'
    
    return final_output

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'error': f'Lỗi đọc file: {str(e)}'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập hoặc upload code LuaU!'}), 400

    is_valid, message = check_syntax(input_code)
    if not is_valid:
        return jsonify({'error': f'Lỗi cú pháp: {message}'}), 400

    try:
        obfuscated = obfuscate(input_code)
        return jsonify({
            'output': obfuscated,
            'status': 'Mã hóa thành công! Code LuaU siêu an toàn (Level Moonsec Premium).'
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi trong quá trình mã hóa: {str(e)}'}), 500

@app.route('/api/check_syntax', methods=['POST'])
def api_check_syntax():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'error': f'Lỗi đọc file: {str(e)}'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập hoặc upload code LuaU!'}), 400

    is_valid, message = check_syntax(input_code)
    return jsonify({'valid': is_valid, 'message': message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
