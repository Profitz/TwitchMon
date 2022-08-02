import PySimpleGUI as sg
import requests
from time import sleep
from threading import Event
import yaml
from yaml.loader import BaseLoader

"""
    Title:  TwitchMon
    Description:  This is a simple twitch monitor which lets you know if one of your favorite streamers
    goes live.  Their channel name you entered will appear in green under LIVE Channels.
    Twitter:  @ProfitzTV
    License:  GNU GPLv3 [https://choosealicense.com/licenses/gpl-3.0/]
    Date of Origination:  2022-07-31 | version 0.1
"""

# TODO Add in UI to add to this list of favorite streamers (update, delete, clear)
# TODO Add an customizable interval timer where the app doesn't make the window inmoveable/frozen
streamers = []
live_chans = []
headings = ['streamer']
sg.theme('GreenMono')


def heart_beat(streamer_list1: list):
    # Queries each streamer in the list to determine if life by using the is_live function
    chan_status = []
    for name in streamer_list1:
        checker = is_live(name)

        if checker == "live":
            chan_status.append(name)

    return chan_status


def is_live(channel_name: str):
    # Scrapes twitch page for chan_live string and returns live if found
    contents = requests.get('https://www.twitch.tv/' + channel_name).content.decode('utf-8')
    chan_live = """"isLiveBroadcast":true"""
    if chan_live in contents:
        return "live"
    else:
        pass


def starting_app():
    status_frame_layout = [
        [sg.Text('App started.', key='-STATUSMSG-', size=25, text_color='black', pad=(5, 5))]
    ]

    frame_layout = [
        [sg.Multiline('', key="-FRAME_LIVE_TEXT-", size=(20, 9), no_scrollbar=True)],
    ]
    main_layout = [
        [sg.Text('Enter streamer name:', size=20), sg.Button('Add', key='-ADD-'), sg.InputText()],
        [sg.Multiline("", write_only=True, key='-MULTI-', autoscroll=True, size=(20, 11),
                      visible=True),
         sg.Frame("LIVE Channels", frame_layout, key='-FRAME-', element_justification='left')],
        [sg.Button('Update', key='-UPDATE-', visible=True),
         sg.Button('Start Monitoring', key='-STARTMON-', visible=True),
         sg.Button('Close')],
        [sg.Frame("Status Message", status_frame_layout, key='-STATUSFRAME-', element_justification='left')],
    ]

    window = sg.Window("Your Favorite LIVE Streamer Monitor", main_layout, size=(450, 350), finalize=True)

    # load streamers yaml file here to multiline box
    with open('streamers.yaml') as f:
        data = yaml.load_all(f, Loader=BaseLoader)
        for i in data:
            window['-MULTI-'].update(i + "\n", append=True)
            streamers.append(i)
            print("reading yaml: ", i)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Close':
            break

        if event == '-UPDATE-':
            # TODO if check on yaml file to see if empty first, if not, update with list
            print("first time in update: ", streamers)
            # take what is listed in the multi-line and overwrite yaml file
            with open('streamers.yaml', 'w') as f:
                yaml.dump_all(streamers, f, sort_keys=True)

            print("update streamers list: ", streamers)
            # TODO provide a status of what happened during the update (example: added 2, or removed x)

        if event == '-ADD-':
            streamers.append(values[0])
            streamers.sort()
            window['-MULTI-'].update("\n" + values[0], append=True)
            window.refresh()
            print('printing streamers on add:', streamers)
            with open('streamers.yaml', 'w') as f:
                yaml.dump_all(streamers, f, sort_keys=True)

        if event == '-STARTMON-':
            # check and read yaml file
            while True:
                run_live_check = heart_beat(streamers)
                run_live_check.sort()
                for streamer in run_live_check:
                    window['-FRAME_LIVE_TEXT-'].update(streamer + "\n", append=True, autoscroll=True,
                                                       text_color='white',
                                                       background_color_for_value='green')
                    window.refresh()
                # TODO update this somehow where it doesn't freeze the app
                # sleep(10)
                # Event().wait(10)
                window['-FRAME_LIVE_TEXT-'].update("")
    window.close()


starting_app()
