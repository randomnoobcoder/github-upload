from google.cloud import mediatranslation
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'media-translation-key.json'


def translate_from_file(file_path):
    client = mediatranslation.SpeechTranslationServiceClient()

    # The `sample_rate_hertz` field is not required for FLAC and WAV (Linear16)
    # encoded data. Other audio encodings must provide the sampling rate.
    audio_config = mediatranslation.TranslateSpeechConfig(
        audio_encoding='linear16',
        source_language_code='en-US',
        target_language_code='fr-FR')

    streaming_config = mediatranslation.StreamingTranslateSpeechConfig(
        audio_config=audio_config, single_utterance=True)

    def request_generator(config, audio_file_path):

        # The first request contains the configuration.
        # Note that audio_content is explicitly set to None.
        yield mediatranslation.StreamingTranslateSpeechRequest(
            streaming_config=config, audio_content=None)

        with open(audio_file_path, 'rb') as audio:
            while True:
                chunk = audio.read(4096)
                if not chunk:
                    break
                yield mediatranslation.StreamingTranslateSpeechRequest(
                    audio_content=chunk,
                    streaming_config=config)

    requests = request_generator(streaming_config, file_path)
    responses = client.streaming_translate_speech(requests)

    for response in responses:
        # Once the transcription settles, the response contains the
        # is_final result. The other results will be for subsequent portions of
        # the audio.
        result = response.result
        translation = result.text_translation_result.translation
        source = result.recognition_result

        print('result : {}'.format(result))
        print('translation : {}'.format(translation))
        print('source : {}'.format(source))

        if result.text_translation_result.is_final:
            print(u'\nFinal translation: {0}'.format(translation))
            print(u'Final recognition result: {0}'.format(source))
            break

        print(u'\nPartial translation: {0}'.format(translation))
        print(u'Partial recognition result: {0}'.format(source))


file = 'data\\testaudio.mp3'

translate_from_file(file)
