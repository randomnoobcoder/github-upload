import io
from multiprocessing import Pool
from google.cloud import videointelligence
from google.cloud.videointelligence import enums, types
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key.json'
video1 = 'gs://shot-change-detection/cctv_test.mp4' # 'data\\vid1.mp4'
video2 = 'data\\vid2.mp4'
inputs = [video1, video2]


def label_detection_vid(video_uri):
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [enums.Feature.LABEL_DETECTION]
    operation = video_client.annotate_video(
        input_uri=video_uri,
        features=features)
    result = operation.result(timeout=90)
    print('\nFinished processing.')
    segment_labels = result.annotation_results[0].segment_label_annotations
    for i, segment_label in enumerate(segment_labels):
        print('Video label description: {}'.format(
            segment_label.entity.description))
        for category_entity in segment_label.category_entities:
            print('\tLabel category description: {}'.format(
                category_entity.description))

        for i, segment in enumerate(segment_label.segments):
            start_time = (segment.segment.start_time_offset.seconds +
                          segment.segment.start_time_offset.nanos / 1e9)
            end_time = (segment.segment.end_time_offset.seconds +
                        segment.segment.end_time_offset.nanos / 1e9)
            positions = '{}s to {}s'.format(start_time, end_time)
            confidence = segment.confidence
            print('\tSegment {}: {}'.format(i, positions))
            print('\tConfidence: {}'.format(confidence))
        print('\n')


label_detection_vid(video1)
