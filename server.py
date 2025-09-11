import random
import string
import re
from flask import Flask, request, jsonify
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
def generate_random_name(length=2):
    """Tạo tên ngẫu nhiên với độ dài chỉ định"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def multi_layer_xor(data, layers=2):
    """Mã hóa nhiều lớp XOR với các key ngẫu nhiên - tối ưu hóa"""
    encrypted_data = data.encode()
    keys = []
    
    for _ in range(layers):
        key_len = random.randint(3, 8)
        key = bytes([random.randint(1, 255) for _ in range(key_len)])
        encrypted_data = bytes([b ^ key[i % key_len] for i, b in enumerate(encrypted_data)])
        keys.append(key)
    
    return encrypted_data, keys

def generate_junk_statements(count=5):
    """Tạo các câu lệnh rác ngẫu nhiên để chèn vào code"""
    junk_templates = [
        "if {} then local {}={} end",
        "for {}={},{} do local {}={} end",
        "while {} do break end",
        "repeat until {}",
        "local {}={}",
        "local function {}(...) return {} end",
        "{}={}",
        "do local {}={} end"
    ]
    
    junk_statements = []
    for _ in range(count):
        template = random.choice(junk_templates)
        vars_needed = template.count('{}')
        vars = [generate_random_name() for _ in range(vars_needed)]
        
        # Tạo giá trị ngẫu nhiên
        values = []
        for i in range(vars_needed):
            if i % 3 == 0:
                values.append(str(random.randint(1, 100)))
            elif i % 3 == 1:
                values.append(f'"{generate_random_name(4)}"')
            else:
                values.append(random.choice(['true', 'false', 'nil']))
        
        junk_statements.append(template.format(*values))
    
    return junk_statements

def obfuscate_names(code):
    """Đổi tên biến và hàm thành tên ngẫu nhiên - cải tiến"""
    # Tìm tất cả các biến và hàm không phải từ khóa
    pattern = r'\b(?!local|function|end|if|then|else|elseif|for|while|do|repeat|until|return|break|true|false|nil|and|or|not|in)([a-zA-Z_][a-zA-Z0-9_]*)\b'
    identifiers = set(re.findall(pattern, code))
    
    # Tạo ánh xạ tên mới
    mapping = {}
    for identifier in identifiers:
        # Giữ nguyên các phương thức đối tượng (dạng obj:method)
        if ':' in identifier:
            continue
        mapping[identifier] = generate_random_name()
    
    # Thay thế tên
    for old_name, new_name in mapping.items():
        code = re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, code)
    
    return code

def flatten_code(code):
    """Làm phẳng mã: xóa comment, khoảng trắng thừa, xuống dòng"""
    # Xóa comment
    code = re.sub(r'--.*$', '', code, flags=re.MULTILINE)
    
    # Xóa khoảng trắng thừa và xuống dòng
    code = re.sub(r'\s+', ' ', code)
    code = re.sub(r'\s*([\(\)\{\}\[\]=,;+\-*/%])\s*', r'\1', code)
    
    return code.strip()

def insert_junk_code(code, junk_count=5):
    """Chèn mã rác vào các vị trí ngẫu nhiên trong code"""
    lines = code.split(';')
    if len(lines) <= 1:
        return code
    
    junk_statements = generate_junk_statements(junk_count)
    
    # Chèn junk code vào các vị trí ngẫu nhiên
    for junk in junk_statements:
        pos = random.randint(0, len(lines) - 1)
        lines.insert(pos, junk)
    
    return ';'.join(lines)

def generate_decryption_code(encrypted_data, keys):
    """Tạo mã giải mã ngắn gọn và hiệu quả"""
    # Chuyển dữ liệu đã mã hóa thành chuỗi byte
    byte_array = ','.join(str(b) for b in encrypted_data)
    
    # Tạo mã giải mã
    decryption_code = []
    
    # Tạo key strings
    for i, key in enumerate(keys):
        key_str = '{' + ','.join(str(b) for b in key) + '}'
        decryption_code.append(f'local k{i}={key_str}')
    
    # Tạo mã giải mã
    decryption_code.append(f'local d=string.char(unpack({{{byte_array}}}))')
    
    # Giải mã từng lớp
    for i in range(len(keys)-1, -1, -1):
        key_len = len(keys[i])
        decryption_code.append(f'd=d:gsub(".",function(c)return string.char(c:byte()~k{i}[(c:byte()%{key_len})+1])end)')
    
    decryption_code.append('loadstring(d)()')
    
    return ';'.join(decryption_code)

def obfuscate_luau(code, junk_amount=5, xor_layers=2):
    """Hàm chính để obfuscate mã Luau - phiên bản tối ưu"""
    try:
        # Bước 1: Đổi tên biến và hàm
        code = obfuscate_names(code)
        
        # Bước 2: Làm phẳng mã
        code = flatten_code(code)
        
        # Bước 3: Chèn mã rác
        code = insert_junk_code(code, junk_amount)
        
        # Bước 4: Mã hóa nhiều lớp XOR
        encrypted_data, keys = multi_layer_xor(code, xor_layers)
        
        # Bước 5: Tạo mã giải mã và thực thi
        final_code = generate_decryption_code(encrypted_data, keys)
        
        return final_code
    
    except Exception as e:
        raise Exception(f"Lỗi khi obfuscate: {str(e)}")

@app.route('/obfuscate', methods=['POST'])
def obfuscate():
    """Endpoint để obfuscate mã Luau"""
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
        
        code = data['code']
        junk_amount = data.get('junk_amount', 5)
        xor_layers = data.get('xor_layers', 2)
        
        obfuscated_code = obfuscate_luau(code, junk_amount, xor_layers)
        
        return jsonify({
            'obfuscated_code': obfuscated_code,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint kiểm tra tình trạng server"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
