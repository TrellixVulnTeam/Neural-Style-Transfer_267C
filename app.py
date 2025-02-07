import io
import json
import os

##########################
# turn pytorch model to api
#########################
from base64 import encodebytes

import torch
from torchvision import transforms
from PIL import Image
import re
from flask import Flask, jsonify, request, send_file

from transformer_net import TransformerNet
from utils import save_image

app = Flask(__name__)

cuda = int(0)
device = torch.device("cuda" if cuda else "cpu")
trained_model_path = 'saved_model/rain_night.pth'
output_image_path = 'images/output/out4.jpg'


# when sending an RGB image
def transform_image(infile):
    # use multiple TorchVision transforms to ready the image
    my_transforms = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    # Open the image file
    # image = Image.open(infile)
    image = Image.open(infile).convert('RGB')
    # Transform PIL image to appropriately-shaped PyTorch tensor
    timg = my_transforms(image)
    # PyTorch models expect batched input; create a batch of 1
    timg = timg.unsqueeze(0).to(device)
    return timg


# apply the trained model on content image
def get_output(trained_model, content_image):
    with torch.no_grad():
        style_model = TransformerNet()
        state_dict = torch.load(trained_model)
        # remove saved deprecated running_* keys in InstanceNorm from the checkpoint
        for k in list(state_dict.keys()):
            if re.search(r'in\d+\.running_(mean|var)$', k):
                del state_dict[k]
        style_model.load_state_dict(state_dict)
        style_model.to(device)
        output = style_model(content_image).cpu()
        # utils.save_image(args.output_image, output[0])
    return output


def get_response_image(image_path):
    # reads the PIL image
    pil_img = Image.open(image_path, mode='r')
    # convert the PIL image to byte array
    byte_arr = io.BytesIO()
    pil_img.save(byte_arr, format='JPEG')
    # encode as base64
    encoded_img = encodebytes(byte_arr.getvalue()).decode('ascii')
    return encoded_img


# !python3 "neural_style.py" eval --content-image './image1.jpg' --model './rain_princess.pth' --output-image './output/out1.jpg' --cuda 1

@app.route('/', methods=['GET'])
def root():
    return jsonify({'msg': 'Try POSTing to the /generate endpoint with an RGB image attachment'})


@app.route('/generate', methods=['POST'])
def generate():
    if request.method == 'POST':
        file = request.files['image']
        if file is not None:
            input_tensor = transform_image(file)
            output_tensor = get_output(trained_model_path, input_tensor)
            output_image = save_image(output_image_path, output_tensor[0])
            # return send_file(output_image_path, mimetype='image/jpg')
            encoded_img = get_response_image(output_image_path)
            response = {'image': encoded_img}
            return jsonify(response)


###########################
# code to test connection with android app
###########################
#
# from flask import Flask, request, jsonify
#
# app = Flask(__name__)
#
#
# # root
# @app.route("/")
# def index():
#     """
#     this is a root dir of my server
#     :return: str
#     """
#     return "This is root!!!!"
#
#
# # GET
# @app.route('/users/<user>')
# def hello_user(user):
#     """
#     this serves as a demo purpose
#     :param user:
#     :return: str
#     """
#     return "Hello %s!" % user
#
#
# # POST
# @app.route('/api/post_some_data', methods=['POST'])
# def get_text_prediction():
#     """
#     predicts requested text whether it is ham or spam
#     :return: json
#     """
#     json = request.get_json()
#     print(json)
#     if len(json['text']) == 0:
#         return jsonify({'error': 'invalid input'})
#
#     return jsonify({'you sent this': json['text']})

###########################

# running web app in local machine
# server on http://0.0.0.0:5000/
# visible across the network
# BaseUrl for Android http://<your ip address>:5000/...
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# development way
# server on http://127.0.0.1:5000/
# (invisible across the network) won't work on other device, other than development machine
# if __name__ == '__main__':
#     app.run()
