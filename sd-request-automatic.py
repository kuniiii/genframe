import zmq
import sd_request_progress

def main():
    txt2img_url = 'http://0.0.0.0:7861/sdapi/v1/txt2img'
    data = {
        'prompt': 'a cat wearing a hat, oil on canvas',
        'steps': 30,
        'enable_hr': 'true',
        'denoising_strength': 0.7,
        'firstphase_width': 512,
        'firstphase_height': 512,
        'hr_scale': 2,
        'hr_upscaler': 'ESRGAN_4x',
        'hr_resize_x': 1024,
        'hr_resize_y': 1024
    }

    progressapi_url = 'http://0.0.0.0:7861/sdapi/v1/progress'

    context = zmq.Context()
    output_socket = context.socket(zmq.PUB)
    output_socket.bind("tcp://*:5556")  # Bind to a different port

    sd_request_progress.run_process_txt2img(txt2img_url, data, progressapi_url, output_socket)

    # Clean up ZeroMQ resources
    output_socket.close()
    context.term()

if __name__ == '__main__':
    main()