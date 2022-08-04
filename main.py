import _thread
import PySimpleGUI as sg
import requests
import schedule
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

# TODO Add update, delete, clear functionality on streamers list
# TODO Add an customizable interval timer where the app doesn't make the window unmovable/frozen
streamers = []
headings = ['streamer']
sg.theme('GreenMono')


def func(window):
    global i
    window.write_event_value('Update', i)
    i = 1


def new_thread(window, event, values):
    global running
    schedule.every(5).seconds.do(func, window=window)
    running = True
    while running:
        schedule.run_pending()
        stream_mon()


def stream_mon():
    run_live_check = heart_beat(streamers)
    run_live_check.sort()
    # change button text to Stop Monitoring
    window['-STARTMON-'].update(text='Stop Monitoring')
    if len(run_live_check) == 0:
        window['-STATUSMSG-'].update("No live streamers atm", text_color='red')
        window.refresh()
    else:
        window['-STATUSMSG-'].update("Streamers are live.", text_color='green')
        window.refresh()
    window['-FRAME_LIVE_TEXT-'].update("")
    for streamer in run_live_check:
        # TODO turn these into URL links
        # TODO add their avatar instead of or beside their name?
        window['-FRAME_LIVE_TEXT-'].update(streamer + "\n", append=True, autoscroll=True,
                                           text_color='white', background_color_for_value='green')
    window.refresh()
    # webbrowser.open('https://www.twitch.tv/' + streamer + '/')


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
    # load streamers yaml file here to multiline box
    with open('streamers.yaml') as f:
        data = yaml.load_all(f, Loader=BaseLoader)
        for i in data:
            window['-MULTI-'].update(i + "\n", append=True)
            streamers.append(i)
    f.close()
    while True:
        """Detect window events"""
        event, values = window.read(timeout=10)
        if event == sg.WIN_CLOSED or event == 'Close':
            running = False
            break

        if event == '-UPDATE-':
            # take what is listed in the multi-line and overwrite yaml file
            with open('streamers.yaml', 'w') as f:
                yaml.dump_all(streamers, f, sort_keys=True)
            f.close()
            # TODO provide a status of what happened during the update (example: added 2, or removed x)

        if event == '-ADD-':
            streamers.append(values[0])
            streamers.sort()
            window['-MULTI-'].update("\n" + values[0], append=True)
            window.refresh()
            with open('streamers.yaml', 'w') as f:
                yaml.dump_all(streamers, f, sort_keys=True)
            f.close()

        if event == '-STARTMON-':
            _thread.start_new_thread(new_thread, (window, event, values))
            # TODO if button is pressed twice, disable/toggle?

    window.close()


if __name__ == "__main__":
    # LAYOUT CREATION
    status_frame_layout = [
        [sg.Text('App started.', key='-STATUSMSG-', size=25, text_color='black', pad=(5, 5))]
    ]

    frame_layout = [
        [sg.Multiline('', key="-FRAME_LIVE_TEXT-", size=(25, 10), no_scrollbar=True)],
    ]
    main_layout = [
        [sg.Text('Enter streamer name:', size=20), sg.Button('Add', key='-ADD-'), sg.InputText()],
        [sg.Multiline("", write_only=True, key='-MULTI-', autoscroll=True, size=(25, 11),
                      visible=True),
         sg.Frame("LIVE Channels", frame_layout, key='-FRAME-', element_justification='left')],
        [sg.Button('Update', key='-UPDATE-', visible=True),
         sg.Button('Start Monitoring', key='-STARTMON-', visible=True),
         sg.Button('Close')],
        [sg.Frame("Status Message", status_frame_layout, key='-STATUSFRAME-', element_justification='left')],
    ]
    # TODO make window scalable/resizable and dynamic
    window = sg.Window("Your Favorite LIVE Streamer Monitor", main_layout, size=(450, 350), finalize=True,
                       icon='twitchmon.ico', border_depth=5, keep_on_top=True)  # scaling=True
    i = 0
    threads = []

    starting_app()
