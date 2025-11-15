#!/usr/bin/env nix-shell
#!nix-shell --pure -i python3 -p python3Packages.Wand

# Normal imports
import os
import re
import shutil
import zipfile
import argparse

from wand.api import library as WandLibrary
from wand.color import Color as WandColor
from wand.image import Image as WandImage

# Project Configuration
import config


def iprint(*strin, success=False) -> None:
    print("[%s %s %s]" % (
        "\033[93;1m" if not success else "\033[92;1m",
        "!" if not success else "✓", "\033[0m"
    ), *strin)


def build_android(local_path, default_assets_path, distribute_path, bottom_imgs):
    iprint("Loading resolutions")

    # Store the different types of top images
    top_imgs_ref = {}

    iprint("Loading and resizing top part of images")

    # Create the top image for each custom resolution
    for name, resolutions in config.RESOLUTIONS.items():
        # The size of the top must the 1/3 of the smallest side
        top_size = int(min(resolutions) / 3)

        # Load the top image
        top_img = WandImage()
        with WandColor("transparent") as background_color:
            WandLibrary.MagickSetBackgroundColor(
                top_img.wand, background_color.resource
            )
        top_img.read(filename=os.path.join(local_path, config.LOGO_IMAGE))
        # Needs to be a square
        top_img.resize(top_size, top_size)

        # Store the data
        top_imgs_ref[name] = top_img

    iprint("Counting and loading bottom part of images")

    # Get the bottom parts
    bottom_imgs_ref = []

    # Iterate the bottom images and load them into memory
    for each_img in bottom_imgs:
        bottom_imgs_ref.append(WandImage(filename=os.path.join(default_assets_path, each_img)))

    # Files structure
    images = {}

    iprint("Assembling images")

    # Assemble all the images
    for name, each_top in top_imgs_ref.items():
        # Images for a specific resolution
        specific_images = []
        for each_bottom in bottom_imgs_ref:
            # The new width should be the one of the bigger image
            new_width = max(each_top.width, each_bottom.width)
            # The new height should be the sum of all plus a responsive spacing
            new_height = int(each_top.height + (each_top.height / 2) + each_bottom.height)

            # Create the new image with the new dimensions
            new_img = WandImage(width=new_width, height=new_height)

            # Calculate the center offsets
            top_offset = int((new_width / 2) - (each_top.width / 2))
            bottom_offset = int((new_width / 2) - (each_bottom.width / 2))

            # Add the images
            new_img.composite(image=each_top, left=top_offset, top=0)
            new_img.composite(image=each_bottom, left=bottom_offset, top=(new_height - each_bottom.height))

            # Add the generated image to the list
            specific_images.append(new_img)

        # Append it all to the images
        images[name] = {
            "resolutions": config.RESOLUTIONS[name],
            "list": specific_images
        }

    iprint(f"Generating {config.DESCRIPTION_FILE} files")

    # Create the description files
    for name, each in images.items():
        string = "%s\n%s\n" % (
            "%d %d %d" % (
                each["list"][0].width,
                each["list"][0].height,
                config.RESOLUTIONS[name][2]
            ),
            "%c %d %d %s" % ('p', 0, 0, config.FOLDER_NAME)
        )
        each["description"] = string

    iprint("Creating output directories")

    # Create the bootanimations
    for name, each in images.items():
        ref_path = os.path.join(distribute_path, config.ANDROID_FOLDER, name)
        each["path"] = ref_path
        if os.path.exists(ref_path):
            shutil.rmtree(ref_path)
        os.makedirs(ref_path)

    iprint("Zipping files")

    # Create the zip files
    for name, each in images.items():
        zip_now = zipfile.ZipFile(
            os.path.join(each["path"], config.OUTPUT_NAME), 'w',
            compression=zipfile.ZIP_STORED
        )

        # Add the description file
        zip_now.writestr(config.DESCRIPTION_FILE, each["description"])

        # Iterate the images and write them to the zip
        for index, each_img in enumerate(each["list"]):
            zip_now.writestr(
                os.path.join(config.FOLDER_NAME, "part%05d.png" % index),
                each_img.make_blob("png")
            )

        # Close the zip
        zip_now.close()

    iprint("Done Android", success=True)


def build_plymouth(local_path, default_assets_path, default_script_path, default_extras_path, distribute_path, bottom_imgs):
    iprint("Creating plymouth theme")

    # Create the folder
    plym = os.path.join(distribute_path, config.PLYMOUTH_FOLDER)
    if os.path.exists(plym):
        shutil.rmtree(plym)
    os.makedirs(plym)

    # Copy throbber files over
    for each_file in os.listdir(default_assets_path):

        # Get the full path of the file
        full_file_name = os.path.join(default_assets_path, each_file)

        # Check if is a file
        if os.path.isfile(full_file_name):

            # Fix names
            throbbed_fixed = re.sub(config.PLYMOUTH_THROBBER, "throbber-", each_file)

            # Reassign
            src = full_file_name
            dst = os.path.join(plym, throbbed_fixed)

            # Check if links
            if os.path.islink(src):
                os.symlink(os.readlink(src), dst)
            else:
                # Copy over
                shutil.copy(src,dst)

    # Copy extra files over
    for each_file in os.listdir(default_extras_path):

        # Get the full path of the file
        full_file_name = os.path.join(default_extras_path, each_file)

        # Check if is a file
        if os.path.isfile(full_file_name):

            # Reassign
            src = full_file_name
            dst = os.path.join(plym, each_file)

            # Check if links
            if os.path.islink(src):
                os.symlink(os.readlink(src), dst)
            else:
                # Copy over
                shutil.copy(src, dst)

    # Resize the logo
    top_img = WandImage()
    with WandColor("transparent") as background_color:
        WandLibrary.MagickSetBackgroundColor(
            top_img.wand, background_color.resource
        )
    top_img.read(filename=os.path.join(local_path, config.LOGO_IMAGE))
    # Needs to be a square
    top_img.resize(config.LOGO_SIZE, config.LOGO_SIZE)
    top_img.save(filename=os.path.join(plym, config.LOGO_IMAGE))

    # Replace and copy over the main plymouth file
    original_name = f"{config.DEFAULT_THEME}.plymouth"
    target_name = f"{config.PLYMOUTH_THEME}.plymouth"
    file_path = os.path.join(default_script_path, original_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as original:

            # Read the entire file
            file_text = original.read()

            # Replace everything
            for repl_name, repl_value in config.REPLACE_PLYMOUTH.items():
                file_text = re.sub(
                    f"{config.FIND_CHAR}{repl_name}{config.FIND_CHAR}",
                    repl_value,
                    file_text
                )

            # Open the target
            with open(os.path.join(plym, target_name), 'w') as target:
                # Write it
                target.write(file_text)

    # Replace and copy over the main script file
    original_name = f"{config.DEFAULT_THEME}.script"
    target_name = f"{config.PLYMOUTH_THEME}.script"
    file_path = os.path.join(default_script_path, original_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as original:

            # Read the entire file
            file_text = original.read()

            # Add manual values
            replace_all = {
                "NUM_IMAGES": str(len(bottom_imgs)),
                **config.REPLACE_SCRIPT
            }

            # Replace everything
            for repl_name, repl_value in replace_all.items():
                file_text = re.sub(
                    f"{config.FIND_CHAR}{repl_name}{config.FIND_CHAR}",
                    repl_value,
                    file_text
                )

            # Open the target
            with open(os.path.join(plym, target_name), 'w') as target:
                # Write it
                target.write(file_text)

    iprint("Done Plymouth", success=True)


def main():
    # Arguments
    parser = argparse.ArgumentParser(
        description="Build boot animation for my systems"
    )
    default_argument = "all"
    parser.add_argument(
        "system",
        choices=[default_argument, config.ANDROID_FOLDER, config.PLYMOUTH_FOLDER],
        default=default_argument,
        nargs='?',
        help="Select system"
    )
    args = parser.parse_args()

    # Get our path
    local_path = os.path.dirname(__file__)

    # Join the path of the main assets
    default_assets_path = os.path.join(
        local_path, "assets", "themes", config.DEFAULT_THEME
    )
    default_script_path = os.path.join(
        local_path, "assets", "scripts"
    )
    default_extras_path = os.path.join(
        local_path, "assets", "extra"
    )
    distribute_path = os.path.join(
        local_path, config.DISTRIBUTE
    )

    # Get all the images
    bottom_imgs = sorted([name for name in os.listdir(default_assets_path) if "bottom" in name])

    # Call functions
    if args.system in [default_argument, config.ANDROID_FOLDER]:
        build_android(local_path, default_assets_path, distribute_path, bottom_imgs)

    if args.system in [default_argument, config.PLYMOUTH_FOLDER]:
        build_plymouth(local_path, default_assets_path, default_script_path, default_extras_path, distribute_path, bottom_imgs)


if __name__ == "__main__":
    main()
