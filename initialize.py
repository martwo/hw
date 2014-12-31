from hw import core
def print_center(s, f='', b=''):
    text = f
    remaining_len = 80 - len(f+s+b)
    text += remaining_len/2*' '
    text += s
    text += remaining_len/2*' '
    text += b
    print(text)
print_center("================================================================================")
print_center("Welcome to the Howling Wolf program V%s"%(core.__version__), '|', '|')
print_center("================================================================================")
