# visual-scout (🚧 WIP)

A work-in-progress tool for extracting visual elements (objects and text) from a set of videos, using OpenAI.

## Requirements

Before installing `visual-scout`, ensure your system has:

### 1. **python >= 3.8:**

- To check this run the following and ensure a valid python version is shown: 

```
python3 --version
```

### 2. **FFmpeg and FFprobe**: 

- These command-line tools are required for:
    - Extracting frames from videos (ffmpeg)
    - Inspecting video metadata like duration (ffprobe)

- Install on MacOS (using Homebrew):

```
brew install ffmpeg
```

- Or, Install on Ubuntu/Debian:

```
sudo apt update
sudo apt install ffmpeg
```

### 3. **pipx**

_Note:_ pipx is a tool for installing and running Python applications in isolated environments. It ensures that each CLI tool has its own clean environment, separate from your global Python packages. Once installed with pipx, you can run the CLI from anywhere on your computer, just like a native system command.

#### Option 1 - Basic install:

```
python3 -m pip install --user pipx

# Confirm install and add the installed scripts to your shell's PATH:
python3 -m pipx ensurepath
```

#### Option 2 - Install with Homebrew:

```
brew install pipx

# Confirm install and add the installed scripts to your shell's PATH:
pipx ensurepath
```

**Open a new terminal window to ensure all install changes take effect.**

## **Install `visual-scout`**

###  1. Install package from github source

_Note: Eventually, Visual Scout will be published to PyPI._

- The install command will:
    - Clone the Visual Scout repository from GitHub
    -  Install it into an isolated virtual environment
    - Make the visual-scout command available globally on your system

#### Option 1 - Basic install

```
python3 -m pipx install git+https://github.com/paigemoody/visual-scout.git
```

#### Option 2 - Use Homebrew

```
pipx install git+https://github.com/paigemoody/visual-scout.git
```


### 4. **Verify installation**

```
visual-scout --help
```

# Process Data

Note: This CLI is still under construction - for now there are four commands that must be run sequentially to generate output data.

## `estimate-cost`

### Usage 
This is a _rough_ estimate based on napkin math of processing cost. For more details on how this works see the write up issue: https://github.com/paigemoody/visual-scout/issues/7.

This command generates a cost estimate to process all videos, gifs and images in a given input dir.

```
    visual-scout estimate-cost <path to your input dir>
```

### Arguments

- `input_dir` (required):
    - Path to the directory containing video/image files.
    - Example: `visual_scout/example_input`

### Example

To use example input directory containing example media files run: 

```
    visual-scout estimate-cost visual_scout/example_input
```

## `extract-frames`

### Usage

This process extracts frames from each video in the given directory and writes each image to a newly created `output/output_frames/` directory, in a subdirectory corresponding to the input file name.

By default the process uses a 'smart sampling' method to reduce the number of sufficiently similar frames by comparing frames at two second intervals. 'Smart sampling' leverages Structural Similarity Index and is valuable for reducing the volume of data sent in subsequent steps to OpenAI, reducing cost and processing time (more docs on this TK). To bypass opt out of smart sampling in favor of sampling at a static interval see optional arguments below.

```
    visual-scout extract-frames <your directory path> [options]
```

## Arguments

- `input_dir` (required):
    - Path to the directory containing video/image files.
    - Example: `visual_scout/example_input`

## Options

- `--use-static-sample-rate` (optional, flag):
    - If set, frames will be sampled every 2 seconds, ignoring content similarity.

- `--similarity` (optional, default=default):
    - Controls strictness of frame similarity comparison, if using "smart sampling".
    - Choices:
        - `strict` (a more conservative approach to filtering out "similar" frames - results in more output frames - )
        - `default`
        - `loose`  (a more aggressive approach to filtering out "similar" frames - results in fewer output frames)

## Example

**Example 1**: You want to extract frames using smart sampling with the default comparison threshold (reccomended).

```
    visual-scout extract-frames <your directory path>
```

*Note: If you want to use example videos to get a sense of the process you can use `visual_scout/example_input` as your directory path.*

**Example 2**: You want to extract frames using smart sampling, but want to be more "strict" about concluding that frames are "suffiently similar". 

```
    visual-scout extract-frames <your directory path> --similarity strict
```

**Example 3**: You want to extract frames using smart sampling, but want to be more aggressive with sampling in order to filter out more frames - you are comforable with deduplicating frames that are loosely similar.

```
    visual-scout extract-frames <your directory path> --similarity loose
```

**Example 4**: You just want to extract frames at 2 second intervals, skipping smart sampling.

```
    visual-scout extract-frames <your directory path> --use-static-sample-rate
```

## Generate Grids 

This process combines extracted frames in the `output/output_frames/` (created in the previous step) into sequential image grids (NxN collages,, defaulting to 3x3). Grid images are written to a newly created directory called `outputs/output_grids/` in a subdirectory named according to the input media file name. 

### Usage

``` 
    visual-scout generate-grids [options]
```

### Options

- `--grid-size` (optional, default=3):
    - Size of the grids (e.g., 3x3).
    - Note that it is reccomended to use the default value for now as OpenAI is the only supported model. 

### Example

```
    visual-scout generate-grids
```

## `generate-labels`

This processes uses an OpenAI model (just OpenAI is supported, for now) to extact information about the visual elements of your videos. It sends each media file's grided frames (generated above and stored in `outputs/output_grids/`) to OpenAI along with a promot which instructs the model to return a json object containing everything it "sees" in the video. 

The output of this command includes:
- An individual json file containing the visual elements for each individual grid file, and 
- One large json file that combines all the individual json files into one json file per input media file, associating each group of elements to their corresponding timestamp.


### Usage

```
    visual-scout generate-labels --open-ai-key <your OpenAI API key> [options]
```

### Arguments

- `--open-ai-key` (required):
    - Your OpenAI API key.
    - To generate an API key, first [create an OpenAI account](https://auth.openai.com/authorize?audience=https%3A%2F%2Fapi.openai.com%2Fv1&auth0Client=eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9&client_id=DRivsnm2Mu42T3KOpqdtwB3NYviHYzwD&device_id=f2886c79-14d0-49c3-8362-82b93d29b456&ext-login-allow-phone=true&ext-use-new-phone-ui=true&issuer=https%3A%2F%2Fauth.openai.com&max_age=0&nonce=cVdJRWJfTzlSSkp0MU8yRTFPRU8xR0FnVWJlRVZzNlRBTGFORGNicXZXSQ%3D%3D&redirect_uri=https%3A%2F%2Fplatform.openai.com%2Fauth%2Fcallback&response_mode=query&response_type=code&scope=openid+profile+email+offline_access&screen_hint=signup&state=QUoxbTZOcHFxdFJ6LkZNX3dvOEtDQ2VyZ3JNbS5iUHYxN2dsdnFYQ21hQQ%3D%3D&flow=treatment), then [generate a new API key](https://platform.openai.com/api-keys)

- `--open-ai-model` (optional, default=gpt-4o-mini):
    - OpenAI model to use for labeling (e.g., `gpt-4o-mini`, `gpt-4o`)
    - Note: 
        - I'd strongly reccomend starting with `gpt-4o-mini` because it works reasonably well and is significantly cheaper (especially important if you'll be processing a lot of videos!).
        - The `cost-estimation` command above estimates processing cost for your dataset for each supported model - a good place to start when chosing which model to use.

### Example

```
visual-scout generate-labels --open-ai-key <your OpenAI API key>
``` 

- Add optional additional arg `--open-ai-model` if you want to specify a model. The default is `gpt-4o-mini`
- This will send the grids produced in the previous step to OpenAI along with a prompt 

# Development Setup

The following is only necessary if you are making changes to the underlying package logic.

1. Create virtual environment

```
python3 -m venv venv
```

2. Activate virtual environment

```
source venv/bin/activate
```

3. Install visual scout in editable mode

```
pipx install -e .
```

4. Confirm installation

```
visual-scout --help
```

5. Run tests

```
pytest
```