# visual-scout

## Setup

1. Create virtual environment

```
python3 -m venv venv
```

2. Activate virtual environment

```
source venv/bin/activate
```

3. Install requirements 

a.  Since opencv-python needs cmake and scikit-build let's install them first

```
pip3 install cmake scikit-build
```

b. Now install the rest

```
pip install -r requirements.txt
```

# Process Video

This process is still under construction - for now there are three sequential processes to run to get output labels.

## Extract Frames 

This process will extract frames from each video in the given directory. Frame images are extracted at 2 second intervals, and written to the `output_frames` directory.

1. Create a directory within `visual_scout` and add all the videos you want to process into the new directory (skip this step if you want to use example videos)

2. Run `python3 -m visual_scout.extract_frames visual_scout/<your directory name>`

    To use example videos: `python3 -m visual_scout.extract_frames visual_scout/example_videos`

