import sys

def modify_train_py(filename):
    with open(filename, 'r') as file:
        content = file.read()

    lines = content.split('\n')

    # Comment out lines 25-29
    for i in range(24, 29):  # 0-based index, so 24 to 28
        if i < len(lines):
            lines[i] = '#' + lines[i]

    # Insert TENSORBOARD_FOUND = False after line 29
    lines.insert(29, 'TENSORBOARD_FOUND = False')

    # Insert import logging and logging configuration after line 30
    lines.insert(30, 'import logging')
    lines.insert(31, '''logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    handlers=[
        logging.StreamHandler()  # 将日志输出到控制台
    ]
)''')

    # Comment out line 56 while preserving existing indentation
    if 56 < len(lines):  
        leading_whitespace = len(lines[56]) - len(lines[56].lstrip())
        lines[56] = lines[56][:leading_whitespace] + '#' + lines[56][leading_whitespace:]

    # Insert the new code block after the new line 134 (original 126 + 8)
    new_code = '''            if iteration % 100 == 0:
                current_gaussians_count = scene.gaussians.get_xyz.shape[0]
                sys.stdout.write("\\r")  # Clear the current line
                sys.stdout.write(
                    f"Iteration: {iteration}/{opt.iterations}, "
                    f"Loss: {ema_loss_for_log:.7f}, "
                    f"Depth Loss: {ema_Ll1depth_for_log:.7f}, "
                    f"Current Gaussians: {current_gaussians_count}"
                )
                sys.stdout.flush()  # Ensure the output is displayed immediately'''
    lines.insert(134, new_code)

    # Comment out lines 128 to 133 while preserving existing indentation
    for i in range(127, 133):  # 0-based index, so 127 to 132
        if i < len(lines):
            # Count leading spaces/tabs
            leading_whitespace = len(lines[i]) - len(lines[i].lstrip())
            # Preserve leading whitespace and add comment symbol
            lines[i] = lines[i][:leading_whitespace] + '#' + lines[i][leading_whitespace:]

    # Join the lines back into a single string
    modified_content = '\n'.join(lines)

    # Write the modified content back to the file
    with open(filename, 'w') as file:
        file.write(modified_content)

    print(f"Successfully modified {filename}")

if __name__ == "__main__":
    modify_train_py('/workspace/gaussian-splatting/train.py')
