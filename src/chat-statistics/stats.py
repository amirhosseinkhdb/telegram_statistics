import json
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
from loguru import logger
from src.data import DATA_DIR
from wordcloud import WordCloud


class ChatStatistics:
    """Generates chat word cloud from a telegram chat json file.
    """

    def __init__(self, chat_json: Union[str, Path]) -> None:
        """
        :param chat_json: telegram chat json file
        """
        logger.info(f"Loading chat data from {chat_json}")
        # load chat data
        with open(chat_json, 'r') as f:
            self.chat_data = json.load(f)

        self.normalizer = Normalizer()

        # load stopwords
        logger.info(f"Loading stopwords from {DATA_DIR / 'stopwords.txt'}")
        stop_words = open(DATA_DIR / 'stopwords.txt').readlines()
        stop_words = list(map(str.strip, stop_words))
        self.stop_words = list(map(self.normalizer.normalize, stop_words))

    def process_text(self, text: str) -> str:
        """Filters and normalizes input text

        :param text: input text to be processed
        :return: processed text
        """
        tokens = word_tokenize(text)
        content = ' '.join(
            list(filter(lambda item: item not in self.stop_words, tokens)))
        content = self.normalizer.normalize(content)
        return content

    def generate_word_cloud(self,
                            output_dir: Union[str, Path],
                            width: int = 800,
                            height: int = 600,
                            background_color: str = 'white'
                            ):
        """Generates a word cloud from the chat data

        :param output_dir: path to output directory for word cloud image
        """

        # append all texts in text_content
        logger.info('Loading text content...')
        text_content = ''
        for msg in self.chat_data['messages']:
            if isinstance(msg['text'], str):
                content = self.process_text(msg['text'])
                text_content += f" {content}"

            elif isinstance(msg['text'], list):
                for item in msg['text']:
                    if isinstance(item, dict):
                        content = self.process_text(item['text'])
                        text_content += f" {content}"
                    else:
                        content = self.process_text(item)
                        text_content += f" {content}"

        # reshape final word cloud
        text_content = arabic_reshaper.reshape(text_content)

        logger.info('Generating word cloud...')
        # generate word cloud
        wordcloud = WordCloud(
            width=width, height=height,
            font_path=str(DATA_DIR / 'Vazir.ttf'),
            background_color=background_color
        ).generate(text_content)

        logger.info(f"Saving word cloud to {output_dir}")
        wordcloud.to_file(Path(output_dir) / 'wordclound.png')


if __name__ == '__main__':
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'ml.json')
    chat_stats.generate_word_cloud(DATA_DIR)
    print("Done!")
