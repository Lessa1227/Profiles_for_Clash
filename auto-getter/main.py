import os
import re
import subprocess
import sys
import time
from threading import Thread
from urllib import request
from urllib.parse import urlencode
from urllib.request import urlretrieve

import yaml
from bs4 import BeautifulSoup

config_file = 'config.yml'


def load_yaml_data(yaml_file, ):
    """读取 YAML 类型文件数据。

    :param yaml_file: 字符串：YAML 文件路径。
    :return: 字典：YAML 文件数据。
    """
    with open(yaml_file, 'r', encoding='utf-8') as data_file:
        content = data_file.read()
    yaml_data = yaml.load(content, Loader=yaml.FullLoader)
    return yaml_data


def rm_dir_files(directory):
    """删除文件夹内部所有文件。

    :param directory: 字符串：要删除内部文件的文件夹。
    :return: 0。
    """
    print('Removing directory ' + directory + '...')
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                print('Removing file ' + name + '...')
                os.remove(os.path.join(root, name))
            for name in dirs:
                print('Removing directory ' + name + '...')
                os.rmdir(os.path.join(root, name))
    else:
        print('The directory ' + directory + ' dos not exits!')


def mkdir(directory):
    """创建文件夹。

    :param directory: 字符串：文件夹路径。
    :return: 0。
    """
    folder = os.path.exists(directory)
    if not folder:
        os.makedirs(directory)
        print('Creating directory' + directory + '...')
    else:
        print('The directory ' + directory + ' exits!')


def save_links(file, link):
    """保存链接。

    :param file: 字符串：文件路径。
    :param link: 字符串：需要保存的链接。
    :return: 0。
    """
    print('Saving links to files...')
    with open(file, 'a', encoding='utf-8') as file:
        file.write(link + '\n')
        file.close()


def remove_repetitive_links(links_stored_file):
    """移除链接存储文件中重复的链接。

    :param links_stored_file: 字符串：文件路径。
    :return: 0。
    """
    print('Removing repetitive links...')
    if os.path.exists(links_stored_file):
        links = []
        for link in open(links_stored_file):
            if link in links:
                print('Repetitive link: ' + link.strip() + '。')
                continue
            links.append(link)
        with open(links_stored_file, 'w') as links_file:
            links_file.writelines(links)
            links_file.close()
    else:
        print('Removing repetitive links failed! No such file: "' + links_stored_file + '".')


def get_shared_links_from_pages(page, tag, attr_class, links_store_file, links_begin_with):
    """从网页元素中获取链接。

    :param page: 字符串：网页链接。
    :param tag: 字符串：网页元素标签。
    :param attr_class: 字符串：网页元素所属类。
    :param links_store_file: 字符串：存储链接的文件。
    :param links_begin_with: 字符串：链接开头。
    :return: 0。
    """
    print('Getting links from tag="' + tag + '" and class="' + attr_class + '"...')
    soup = BeautifulSoup(page, 'html.parser')
    for tag in soup.find_all(tag, class_=attr_class, string=re.compile(links_begin_with)):
        link = tag.get_text().strip()
        print('Acquired link: ' + link + ' .')
        save_links(links_store_file, link)


def get_shared_links_from_files(remote_file, temp_file, links_store_file, links_begin_with):
    """从文件行获取链接。

    :param remote_file: 字符串：远程文件链接。
    :param temp_file: 字符串：临时文件存放路径。
    :param links_store_file: 字符串：链接存储文件。
    :param links_begin_with: 字符串：链接开头。
    :return: 0。
    """
    print('Getting links from ' + remote_file + '...')
    if remote_file != '':
        urlretrieve(remote_file, temp_file)
        with open(temp_file, 'r') as search_file:
            for line in search_file:
                link_list = re.compile(links_begin_with).findall(line)
                if len(link_list) > 0:
                    link = link_list[0]
                    print('Acquired link: ' + link + ' .')
                    save_links(links_store_file, link)
    else:
        print('Remote file is null!')


def get_shared_links(source, links_store_file, links_begin_with):
    """获取分享链接。

    :param: source: 字符串：链接的来源（一般为网页链接）。
    :param: links_store_file: 字符串：存储链接的文件位置。
    :param: links_begin_with: 字符串：链接开头。
    :return: 0。
    """
    print('Getting links from ' + source + '...')
    if source != '':
        headers = {'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.36'}
        req = request.Request(source, headers=headers)
        resp = request.urlopen(req)
        get_shared_links_from_pages(resp, 'p', '', links_store_file, links_begin_with)
        get_shared_links_from_pages(resp, 'div', 'tgme_widget_message_text', links_store_file, links_begin_with)
    else:
        print('Source is null!')


def get_profile_link(parameters, links_stored_file):
    """获取生成配置文件的链接。

    :param parameters: 字典：用于 Sub Converter 的参数。
    :param links_stored_file: 字符串：存储链接的文件的路径。
    :return: 配置文件的链接。
    """
    if os.path.exists(links_stored_file):
        url = ''
        for link in open(links_stored_file):
            url = url + '|' + link.strip()
        parameters['url'] = url
        base_url = 'http://127.0.0.1:25500/sub?'
        profile_link = base_url + urlencode(parameters)
        print('Generating Sub_Converter link: ' + profile_link + ' .')
        return profile_link
    else:
        print('Profile get failed! No such file: "' + links_stored_file + '".')
        return ''


def get_profile(config_path):
    """获取配置。

    :param config_path: 字符串：运行时的配置文件。
    :return: 0。
    """
    # 读取配置数据。
    config = load_yaml_data(config_path)
    others_config = config['others']
    directories_config = others_config['directories']
    links_store_dir = directories_config['links-store-dir']
    profiles_store_dir = directories_config['profiles-store-dir']
    temp_file_store_dir = directories_config['temp-file-store-dir']
    supported_shared_link_begin_with = others_config['supported-shared-link-begin-with']
    supported_subscribe_link_begin_with = others_config['supported-subscribe-link-begin-with']
    sub_converter_config = config['sub-converter']

    # 创建文件夹并删除过时链接文件。
    for directory in directories_config:
        mkdir(directories_config[directory])
        rm_dir_files(directories_config[directory])

    # 根据设置的 Profile 生成配置。
    for profile in config['profiles']:
        # 获取 Profile 信息。
        profile_name = profile['name']
        links_file_path = links_store_dir + '/' + profile_name
        profile_path = profiles_store_dir + '/' + profile_name + '.yml'
        temp_file_path = temp_file_store_dir + '/' + profile_name

        # 生成配置文件。
        print('Getting profile for ' + profile_name + '...')
        for source_type in profile['sources']:
            # 防止配置中该来源类型数值为空。
            if len(profile['sources'][source_type]) > 0:
                print('Source type: ' + source_type + '.')

                # 遍历该来源类型下所有的来源。
                for i in range(0, len(profile['sources'][source_type])):
                    # 获取来源。
                    source = profile['sources'][source_type][i]

                    # 根据来源类型选择相应方法。
                    if source_type == 'pages':
                        get_shared_links(source, links_file_path, supported_shared_link_begin_with)
                    elif source_type == 'tg-channels':
                        if source != '':
                            source = 'https://t.me/s/' + source
                            get_shared_links(source, links_file_path, supported_shared_link_begin_with)
                        else:
                            print('Telegram channel is null!')
                    elif source_type == 'files':
                        get_shared_links_from_files(source, temp_file_path, links_file_path,
                                                    supported_shared_link_begin_with)
                    else:
                        print('Don`t support the source type named "' + source_type + '" now!')
                    time.sleep(3)
            else:
                print(source_type + ' in "' + profile_name + '" is NULL!')

        remove_repetitive_links(links_file_path)

        # 下载配置。
        sub_converter_link = get_profile_link(sub_converter_config, links_file_path)
        if sub_converter_link != '':
            urlretrieve(sub_converter_link, profile_path)
            print('Profile "' + profile_name + '" update complete!')
        else:
            print('Profile "' + profile_name + '" update failed!')


def run_get_profile():
    """运行获取配置文件线程

    :return: 0。
    """
    get_profile(config_file)
    sys.exit()


def run_sub_converter():
    """运行 Sub Converter 线程。

    :return: 0。
    """
    process = subprocess.run(['powershell', './subconverter/subconverter.exe'])


def main():
    """从此处开始运行。

    :return: 0。
    """
    sub_converter = Thread(target=run_sub_converter, daemon=True)
    profile_getter = Thread(target=run_get_profile, daemon=True)
    sub_converter.start()
    profile_getter.start()
    profile_getter.join()


if __name__ == '__main__':
    main()
