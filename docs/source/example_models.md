# Example Models

In order to better understand the process of porting a model to Runway, we recommend checking out the source code for some of the models that have already been ported. All models published by the runway organization are open source, as well as many of the models contributed by our community.

* [Image-Super-Resolution](https://github.com/agermanidis/image-super-resolution): A very simple image upscaling model that gives a good overview of the role of [`runway_model.py`](https://github.com/agermanidis/image-super-resolution/blob/master/runway_model.py).
* [StyleGAN](https://github.com/agermanidis/stylegan): A good example of loading a model checkpoint as well as using the [vector data type](ui_components.html#vector).
* [SPADE-COCO](https://github.com/agermanidis/spade-coco): A good example of the [segmentation data type](ui_components.html#segmentation).
* [DeepLabV3](https://github.com/agermanidis/DeepLabV3): A good example of multiple `@command()` functions and [conditional build steps](https://github.com/agermanidis/DeepLabV3/blob/master/runway.yml) depending on GPU and CPU build environments. Also a very simple model to get started with.
* [Places365](https://github.com/maybay21/model_places365): A good example of a basic image classification task and use of [the text data type](ui_components.html#text) for output.
* [3DDFA](https://github.com/maybay21/3DDFA): A good example of dealing with 3D data as images. We plan to add more features for handling true 3D data.
