import PySimpleGUI as sg
import requests
from time import sleep
from threading import Event

"""
    Title:  TwitchMon
    Description:  This is a simple twitch monitor which lets you know if one of your favorite streamers
    goes live.  Their channel name you entered will appear in green under LIVE Channels.
    Author's Twitter:  @ProfitzTV
    Date of Origination:  2022-07-31 | version 0.1
"""

# TODO Add in UI to add to this list of favorite streamers (add, update, delete)
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
    frame_layout = [
        [sg.Multiline('', key="FRAME_TEXT", size=(20, 9), no_scrollbar=True)],
    ]
    main_layout = [
        [sg.Text('Enter streamer name:', size=20), sg.Button('Add', key='_ADD_'), sg.InputText()],
        [sg.Multiline("[Started service]", write_only=True, key='-MUTLISTATUS-', autoscroll=True, size=(20, 11),
                      visible=True),
         sg.Frame("LIVE Channels", frame_layout, key='FRAME', element_justification='left')],
        [sg.Button('Start Monitoring', key='-STARTMON-', visible=True),
         sg.Button('Close')],
    ]

    # window = sg.Window("Your Favorite LIVE Streamer Monitor", layout, size=(450, 350), finalize=True)
    main_window = sg.Window("Your Favorite LIVE Streamer Monitor", main_layout, size=(450, 350))

    while True:
        event2, main_values = main_window.read()
        if event2 == sg.WIN_CLOSED or event2 == 'Close':
            break
        if event2 == '_ADD_':
            streamers.append(main_values[0])
            streamers.sort()
            # main_window(['-MUTLISTATUS-'].append(main_values[0]))
            main_window['-MUTLISTATUS-'].update("\n" + main_values[0], append=True)
            # main_window.refresh()
            print("streamers:", streamers)
        if event2 == '-STARTMON-':
            while True:
                run_live_check = heart_beat(streamers)
                run_live_check.sort()
                for streamer in run_live_check:
                    main_window['FRAME_TEXT'].update(streamer + "\n", append=True, autoscroll=True, text_color='white',
                                                     background_color_for_value='green')
                    main_window.refresh()
                # TODO update this somehow where it doesn't freeze the app
                #sleep(10)
                Event().wait(10)
                main_window['FRAME_TEXT'].update("")
    main_window.close()


starting_app()
