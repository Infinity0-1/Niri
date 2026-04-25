from os.path import expanduser
import argparse

default_kdl = "~/.config/niri/config.kdl"
default_sep_kb = "\t| "
default_sep_title = " |\t"
default_line_end = "\n"

parser = argparse.ArgumentParser(
    description="Parse niri keybinds into 'dmenu' friendly format",
    epilog="The results from this script can be piped to a launcher for display, eg. using: '| fuzzel -d'",
)
parser.add_argument(
    "-i", "--keybind_kdl", type=str, default=default_kdl, help=f"Path to keybinds.kdl (default: {default_kdl})"
)
parser.add_argument(
    "-t",
    "--exclude_titles",
    action="store_true",
    help="If set, the 'hotkey-overlay-title' text will not be included in the output",
)
parser.add_argument(
    "-s",
    "--include_spawn_prefix",
    action="store_true",
    help="If set, 'spawn' and 'spawn-sh' will be included in the output",
)
parser.add_argument(
    "-c",
    "--include_command_quotes",
    action="store_true",
    help="If set, aprostrophes & quotation marks will not be removed from commands",
)
parser.add_argument("-pk", "--pad_keybind", type=int, default=8, help="Padding added to keybinds (default: 8)")
parser.add_argument("-pt", "--pad_title", type=int, default=32, help="Padding added to titles (default: 32)")
parser.add_argument(
    "-ak",
    "--sep_keybind",
    type=str,
    default=default_sep_kb,
    help=f"Separator after keybind text (default: {default_sep_kb!r})",
)
parser.add_argument(
    "-at",
    "--sep_title",
    type=str,
    default=default_sep_title,
    help=f"Separator after title text (default: {default_sep_title!r})",
)
parser.add_argument(
    "-e",
    "--output_line_end",
    type=str,
    default=default_line_end,
    help=f"Line ending (terminating) string when generating output (default: {default_line_end!r})",
)

args = parser.parse_args()
KEYBIND_KDL_PATH = expanduser(args.keybind_kdl)
INCLUDE_OVERLAY_TITLES = not args.exclude_titles
REMOVE_CMD_QUOTATIONS = not args.include_command_quotes
REMOVE_SPAWN_PREFIX = not args.include_spawn_prefix
PAD_KEYBIND = args.pad_keybind
PAD_TITLE = args.pad_title
SEP_KEYBIND = args.sep_keybind
SEP_TITLE = args.sep_title
OUTPUT_LINE_END = args.output_line_end

try:
    with open(KEYBIND_KDL_PATH, "r") as infile:
        full_text = infile.read()
except FileNotFoundError:
    import subprocess

    notify_title, notify_explain = "Error parsing keybinds!", f"Not found: {KEYBIND_KDL_PATH}"
    subprocess.run(["notify-send", notify_title, notify_explain])
    raise FileNotFoundError(KEYBIND_KDL_PATH)

if full_text.startswith("binds"):
    first_line_break_idx = full_text.index("\n")
    text_after_binds = full_text[1 + first_line_break_idx :]
else:
    before_and_after_binds = full_text.split("\nbinds")
    if len(before_and_after_binds) != 2:
        import subprocess
        notify_title, notify_explain = "Error parsing keybinds!", "Could not find binds {...} section"
        subprocess.run(["notify-send", notify_title, notify_explain])
        raise IOError(f"Error parsing keybinds: {KEYBIND_KDL_PATH}")
    text_after_binds = before_and_after_binds[1]
filtered_list = []

for full_line in text_after_binds.splitlines():
    line = full_line.strip()
    if line == "}":
        break
    if line.startswith("//") or len(line) < 3:
        continue
    config_command_split = line.split("{")
    if len(config_command_split) != 2:
        if len(config_command_split) > 2:
            print("Error parsing keybind! Unexpected double curly bracket:", line, sep="\n", flush=True)
        continue
    config, command = config_command_split
    config_split = config.split(" ", 1)
    command_split = command.split(";")
    keybind_str = config_split[0].ljust(PAD_KEYBIND)
    command_str = command_split[0].strip()
    if REMOVE_SPAWN_PREFIX and command_str.startswith("spawn"):
        command_str = command_str.removeprefix("spawn-sh " if "spawn-sh" in command_str else "spawn ")
    if REMOVE_CMD_QUOTATIONS:
        command_str = command_str.replace('"', "").replace("'", "")
    title_str = ""
    if INCLUDE_OVERLAY_TITLES:
        target_str = "hotkey-overlay-title="
        if target_str in config:
            _, title_split = config.split(target_str)
            if not title_split.startswith("null"):
                str_marker = title_split[0]
                _, title_str, _ = title_split.split(str_marker)
    final_strs = (
        (keybind_str, SEP_KEYBIND, title_str.ljust(PAD_TITLE), SEP_TITLE, command_str)
        if len(title_str) > 0
        else (keybind_str, SEP_KEYBIND, command_str)
    )
    filtered_line = "".join(final_strs)
    filtered_list.append(filtered_line)

print(OUTPUT_LINE_END.join(filtered_list))
