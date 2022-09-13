import json
from collections import defaultdict
from pathlib import Path
from typing import List, Union

import arabic_reshaper
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
        stop_words = map(str.strip, stop_words)
        self.stop_words = set(map(self.normalizer.normalize, stop_words))

    @staticmethod
    def rebuild_msg(msg: list) -> str:
        """Rebuilds input message

        :param msg: input message
        :return: rebuilded message
        """
        msg_text = ''
        for sub_msg in msg:
            if isinstance(sub_msg, dict):
                msg_text += sub_msg['text'] + " "
            else:
                msg_text += sub_msg + " "
        return msg_text

    def msg_has_question(self, msg: dict) -> bool:
        """Checks if a message has a question

        :param msg: message to check
        :return: True if message has question, False else
        """
        text = ''
        if isinstance(msg['text'], str):
            text = msg['text']

        elif isinstance(msg['text'], list):
            text = self.rebuild_msg(msg['text'])

        if '?' in text or '؟' in text:
            return True
        return False

    def get_top_users(self, top_n: int = 10) -> List[tuple]:
        """Get top users from chat data

        :param top_n: numbers of top users, defaults to 10
        :return: users and number of replies as a tuple
        """
        # creating mapping to check which messages are questions
        is_question = defaultdict(bool)
        users = {}
        for msg in self.chat_data['messages']:
            is_question[msg['id']] = self.msg_has_question(msg)

        # Getting top users based on replying to questions by others
        logger.info('Getting top users of chat data...')
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue

            if msg['from_id'] in users.keys():
                users[msg['from_id']]['replies'].append(
                    msg['reply_to_message_id'])

            elif is_question[msg['reply_to_message_id']]:
                users[msg['from_id']] = {
                    'name': msg['from'],
                    'replies': [msg['reply_to_message_id']]
                }

        logger.info('Calculating users with most replies to questions...')
        reply_conut = [(k, len(v['replies'])) for k, v in users.items()]
        users_with_most_replies = [
            (users[user[0]]['name'], user[1]) for user in sorted(
                reply_conut, key=lambda x: x[1], reverse=True
            )
        ]
        return users_with_most_replies[:top_n]

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
            text = ''
            if isinstance(msg['text'], str):
                text = msg['text']
                content = self.process_text(text)
                text_content += f" {content}"

            elif isinstance(msg['text'], list):
                text = self.rebuild_msg(msg['text'])
                content = self.process_text(text)
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
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'ml_2.json')
    chat_stats.generate_word_cloud(DATA_DIR)
    for user in chat_stats.get_top_users(top_n=15):
        print(user)
    print("Done!")
