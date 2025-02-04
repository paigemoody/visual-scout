# visual-scout (🚧 WIP)

A work-in-progress tool for extracting visual elements (objects and text) from a set of videos, using OpenAI.

## Setup

1. Create virtual environment

```
python3 -m venv venv
```

2. Activate virtual environment

```
source venv/bin/activate
```

3. Install initial requirements. Since opencv-python needs cmake and scikit-build we'll install them first:

```
pip3 install cmake scikit-build
```

4. Now install the rest:

```
pip install -r requirements.txt
```

# Process Video

Note: This process is still under construction - for now there are three processes that must be run sequentially to generate output data.

## Extract Frames 

This process will extract frames from each video in the given directory. Frame images are extracted at 2 second intervals, and written to the `output_frames` directory.

1. Create a directory within `visual_scout` and add all the videos you want to process into the new directory (skip this step if you want to use example videos)

2. Run `python3 -m visual_scout.extract_frames visual_scout/<your directory name>`

    To use example videos run: `python3 -m visual_scout.extract_frames visual_scout/example_videos`

## Generate Grids 

This process will combine extracted frames into sequential image grids, defaulting to 3x3 grids. Grid images are written to the `output_grids` directory. 

Note: you may want to play around with grid size to figure out the ideal level of detail required for the specific AI model you're using to extract data from the images.

1. Generate grids

    To use default grid size run: `python3 -m visual_scout.generate_grids`

    To use a different grid size run: `python3 -m visual_scout.generate_grids --grid-size <grid size intger>` 

    For example: `python3 -m visual_scout.generate_grids --grid-size <grid size intger>`

## Extract Visual Content

This is where you will use an AI model (just OpenAI is available for now) to extact information about the visual elements of your videos.

1. Create your .env file

    ```
    cp .env.example .env
    ```

2. Generate an OpenAI API key (skip this if you alredy have one!)

    - [Create an OpenAI account](https://auth.openai.com/authorize?audience=https%3A%2F%2Fapi.openai.com%2Fv1&auth0Client=eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9&client_id=DRivsnm2Mu42T3KOpqdtwB3NYviHYzwD&device_id=f2886c79-14d0-49c3-8362-82b93d29b456&ext-login-allow-phone=true&ext-use-new-phone-ui=true&issuer=https%3A%2F%2Fauth.openai.com&max_age=0&nonce=cVdJRWJfTzlSSkp0MU8yRTFPRU8xR0FnVWJlRVZzNlRBTGFORGNicXZXSQ%3D%3D&redirect_uri=https%3A%2F%2Fplatform.openai.com%2Fauth%2Fcallback&response_mode=query&response_type=code&scope=openid+profile+email+offline_access&screen_hint=signup&state=QUoxbTZOcHFxdFJ6LkZNX3dvOEtDQ2VyZ3JNbS5iUHYxN2dsdnFYQ21hQQ%3D%3D&flow=treatment) 
    - [Generate a new API key](https://platform.openai.com/api-keys)
    - Save API key in your `.env` file as your `OPENAI_KEY` 

3. Determine [which model](https://platform.openai.com/docs/models) you want to use and update your .env to reflect your choice. I'd reccomend starting with `gpt-4o-mini` because it works reasonably well and is significantly cheaper (especially important if you'll be processing a lot of videos!). 

4. Extract visual content by running: `python3 -m visual_scout.extract_visual_content` 

    - This will send the grids produced in the previous step to OpenAI along with a prompt which asks it to return a json object containing everything it sees in the video. 
    - The output is:
        - An individual json file containing the visual elements for one individual grid file, and 
        - One large json file that combines all the individual json files into one, associating each group of elements to their corresponding timestamp. 
