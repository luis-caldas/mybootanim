#!/usr/bin/env python

# Defaults
DEFAULT_THEME = "material"

# Output
DISTRIBUTE = "dist"

########
# Misc #
########

LOGO_IMAGE = "logo.png"

############
# Plymouth #
############

# Paths
PLYMOUTH_FOLDER = "plymouth"
PLYMOUTH_THEME = "main_custom"

# Throbber Name
PLYMOUTH_THROBBER = "bottom"

# Replacing
FIND_CHAR = '%'
REPLACE_SCRIPT = {
    "LOGO_MESSAGE": "",
    "PASS_MSG": "Authenticate",
    "QUESTION_PROMPT": "Answer",
    "PASSWORD_TYPING": "...",
    "PASSWORD_TYPING_ALT": ".",
    "BULLET_CHAR": '•'
}
REPLACE_PLYMOUTH = {
    "PLYMOUTH_THEME": PLYMOUTH_THEME
}

# Sizing
LOGO_SIZE = 128

###########
# Android #
###########

# Paths
ANDROID_FOLDER = "android"

# Paths
FOLDER_NAME = "part0"
DESCRIPTION_FILE = "desc.txt"
OUTPUT_NAME = "bootanimation.zip"

# Resolutions
RESOLUTIONS = {
    "shiba": [1080, 2400, 120],
    "alioth": [1080, 2400, 120],
    "beryllium": [1080, 2246, 60],
    "skipjack": [360, 360, 60]
}
