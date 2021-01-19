from flask import Flask, render_template, request, make_response, jsonify
from google.cloud import videointelligence, storage
from google.cloud.videointelligence import enums
import cv2 as cv
import datetime
import urllib.request as req
import os
# from google.oauth2 import service_account
import shutil

app = Flask(__name__)
app.secret_key = 'random string'
app.config['UPLOAD_FOLDER'] = 'D:\\CodeLab\\Projects\\WebApp\\Uploaded-Files'
key_path = "D:\\CodeLab\\Projects\\WebApp\\key.json"
# key_path = 'key.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
# Explicitly use service account credentials by specifying the private key file.
storage_client = storage.Client().from_service_account_json(key_path)
bucket_name = "shot-change-detection"
bucket = storage_client.get_bucket(bucket_name)


def list_files(input_bucket):
    """List all files in GCP bucket."""
    files = input_bucket.list_blobs()
    file_list = [file.name for file in files if '.' in file.name]
    return file_list


def upload_file(cloud_bucket, filename):
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)
    print('Uploaded file {} to bucket {} '.format(filename, cloud_bucket))
    return filename


def detect_shot_changes(video_uri):
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [enums.Feature.SHOT_CHANGE_DETECTION,
                enums.Feature.LABEL_DETECTION]
    print(f'Processing video "{video_uri}"...')
    operation = video_client.annotate_video(
        input_uri=video_uri,
        features=features,
    )
    return operation.result()


def video_shots(response):
    # First result only, as a single video is processed
    shots = response.annotation_results[0].shot_annotations
    print(shots)
    print(f' Video shots: {len(shots)} '.center(40, '-'))
    for i, shot in enumerate(shots):
        start_ms = shot.start_time_offset.ToMilliseconds()
        end_ms = shot.end_time_offset.ToMilliseconds()
        print(f'{i + 1:>3}',
              f'{start_ms:>7,}',
              f'{end_ms:>7,}',
              sep=' | ')
        print('Change detected..\nTaking Screenshot.... ')
        uploaded_folder_list = os.listdir(app.config['UPLOAD_FOLDER'])
        global test_file
        for file in uploaded_folder_list:
            if file.endswith('.mp4'):
                test_file = file
        directory, captured_file = capture_frames(test_file, end_ms)
        print('Done')
        print("Uploading....")
        full_path = os.path.join(directory, captured_file)
        image_file = full_path.replace('\\', '/')
        upload_file(bucket_name, image_file)


def generate_image_url(blob_path):
    """ generate signed URL of a video stored on google storage.
        Valid for 300 seconds in this case. You can increase this
        time as per your requirement.
    """
    blob = bucket.blob(blob_path)
    return blob.generate_signed_url(datetime.timedelta(minutes=10), method='GET')


def capture_frames(video_path, ms):
    url = generate_image_url(video_path)
    req.urlretrieve(url, video_path)
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f'Could not open video <{video_path}>')
    cap.set(cv.CAP_PROP_POS_MSEC, ms)
    ok, cv_frame = cap.read()
    if not ok:
        raise RuntimeError(f'Failed to get video frame @pos_ms[{ms}]')
    output_folder = 'Captured-Shots'
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    filename = 'shot_change_at_{}.jpg'.format(ms)
    cv.imwrite(os.path.join(output_folder, filename), cv_frame)
    return output_folder, filename


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        if request.files:
            file = request.files['file']
            save_dir = app.config['UPLOAD_FOLDER']
            save_path = os.path.join(save_dir, file.filename)
            file.save(save_path)
            print("File Saved...")
            start_time = datetime.datetime.now()
            print("Started Processing : {} ".format(start_time))
            """
            Upload file to Bucket on cloud
            """
            os.chdir(save_dir)
            upload_file(bucket_name, file.filename)
            """
            Code for Shot Change Detection
            * Getting File Name from Bucket and creating its path
            * Passing the formed path to detect_shot_change function
            """
            video_url = "gs://{}/{}".format(bucket_name, file.filename)

            response = detect_shot_changes(video_url)
            video_shots(response)
            """
            Copying files from Captured Folder to Static Folder
            """
            static_folder = "D:\\CodeLab\\Projects\\WebApp\\static"
            src_dir = os.path.join(app.config['UPLOAD_FOLDER'], "Captured-Shots")
            for file_name in os.listdir(src_dir):
                file_to_copy = os.path.join(src_dir, file_name)
                shutil.copy(file_to_copy, static_folder)
            end_time = datetime.datetime.now()
            print("Processing Done : {} ".format(end_time))

            total_time = end_time - start_time
            print("Total Time Taken in Processing : {} ".format(total_time))
            res = make_response(jsonify({"message": "Done"}), 200)
            return res
            # return redirect(request.url)
    return render_template('analyze.html')
    # return render_template('upload.html')


@app.route('/result')
def result():
    image_names = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'Captured-Shots'))
    print(image_names)
    return render_template("result.html", image_names=image_names)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)

    '''--------------------------------------------'''
