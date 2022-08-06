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

# TODO Add an customizable interval timer where the app doesn't make the window unmovable/frozen
streamers = []
new_values = []
headings = ['streamer']
sg.theme('GreenMono')


def func(window):
    global i
    window.write_event_value('Update', i)
    i = 1


def new_thread(window, event, values):
    global running
    schedule.every(30).seconds.do(func, window=window)
    if event == '-STOPMON-':
        running = False
    elif event == '-STARTMON-':
        running = True
    while running:
        schedule.run_pending()
        stream_mon()


def stream_mon():
    run_live_check = heart_beat(streamers)
    run_live_check.sort()
    # change button text to Stop Monitoring
    if len(run_live_check) == 0:
        window['-STATUSMSG-'].update("There are none of your favorite streamers online.", text_color='red')
        window.refresh()
    else:
        window['-FRAME_LIVE_TEXT-'].update("")
        window.refresh()

    for streamer in run_live_check:
        # TODO turn these into URL links
        # TODO add their avatar instead of or beside their name?
        window['-FRAME_LIVE_TEXT-'].update(streamer + "\n", append=True, autoscroll=True, text_color='white', background_color_for_value='green')
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
    # TODO add in optional for seeing hosted channels - these eventually fall of live query
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

        if event == '-SUBMIT-':
            # read in the value of the drop down
            combo = window['-COMBO-'].get()

            # read in the value of the txt box
            inputtxt = window['-INPUTTXT-'].get()
            if not inputtxt:
                window['-STATUSMSG-'].update('Enter a streamer''\'s name before clicking submit.', text_color='red')
            elif not combo:
                window['-STATUSMSG-'].update('Choose an option from the drop-down before clicking submit.', text_color='red')
            else:
                # perform ADD action
                if combo == 'ADD':
                    streamers.sort()
                    if inputtxt in streamers:
                        window['-STATUSMSG-'].update(inputtxt + " is already in the file.", text_color='red')
                    else:
                        streamers.append(inputtxt)
                        window['-STATUSMSG-'].update("Added: " + inputtxt, text_color='green')
                        window['-MULTI-'].update(inputtxt+'\n', append=True)
                        window.refresh()
                        with open('streamers.yaml', 'w') as f:
                            yaml.dump_all(streamers, f, sort_keys=True)
                        f.close()

                # perform DELETE action
                elif combo == 'DELETE':
                    window['-STATUSMSG-'].update("Removed: " + inputtxt, text_color='green')
                    window.refresh()
                    # remove streamer from yaml and multi
                    # read in yaml, get the index of the streamer and remove from streamer list
                    with open('streamers.yaml', 'r') as f:
                        data_in_file = yaml.load_all(f, Loader=BaseLoader)
                        if inputtxt in data_in_file:
                            index_to_remove = list.index(streamers, inputtxt)
                            streamers.remove(streamers[index_to_remove])
                            window.refresh()
                            f.close()
                            # update the yaml streamer file
                            with open('streamers.yaml', 'w') as f2:
                                yaml.dump_all(streamers, f2, sort_keys=True)
                                window.refresh()
                            f2.close()

                        else:
                            window['-STATUSMSG-'].update(inputtxt + " doesn't exist in the streamer file.", text_color='red')

                else:
                    continue

        # perform STARTMON action
        if event == '-STARTMON-':
            window['-STARTMON-'].update(disabled=True)
            window['-STOPMON-'].update(disabled=False)
            window['-STATUSMSG-'].update("Monitoring started.", text_color='green')
            _thread.start_new_thread(new_thread, (window, event, values))

        # perform STOPMON action
        if event == '-STOPMON-':
            window['-FRAME_LIVE_TEXT-'].update("")
            #window['-LBLIVE-'].update([])
            window['-STATUSMSG-'].update("Monitoring stopped.", text_color='red')
            window['-STOPMON-'].update(disabled=True)
            window['-STARTMON-'].update(disabled=False)
            # window.refresh()
            _thread.start_new_thread(new_thread, (window, event, values))
            continue

    window.close()


if __name__ == "__main__":
    # LAYOUT CREATION
    status_frame_layout = [
        [sg.Text('App started.', key='-STATUSMSG-', size=47, text_color='black', pad=(3, 3))]
    ]
    status_addremove_layout = [
        [sg.InputText('', size=24, key='-INPUTTXT-'), sg.Combo(['ADD', 'DELETE'], key='-COMBO-', auto_size_text=True, readonly=True, size=18),
         sg.Button('Submit', key='-SUBMIT-', visible=True)],
    ]

    frame_layout = [
        [sg.Multiline('', key="-FRAME_LIVE_TEXT-", size=(25, 10), no_scrollbar=True, disabled=True)],
        #[sg.Listbox([], key='-LBLIVE-', size=(25, 10), no_scrollbar=True)],
    ]
    main_layout = [
        [sg.Frame("Enter name of streamer then Add/Delete from dropdown.", status_addremove_layout, key='-FRAMEADDREMOVE-', element_justification='right')],
        [sg.Multiline("", write_only=True, key='-MULTI-', autoscroll=True, size=(25, 11),
                      visible=True, disabled=True),
         sg.Frame("LIVE Channels", frame_layout, key='-FRAME-', element_justification='left')],
        [sg.Button('Start Monitoring', key='-STARTMON-', disabled=False, visible=True),
         sg.Button('Stop Monitoring', key='-STOPMON-', disabled=True, visible=True),
         sg.Button('Close')],
        [sg.Frame("Status Message", status_frame_layout, key='-STATUSFRAME-', element_justification='left')],
    ]
    # TODO make window scalable/resizable and dynamic
    window = sg.Window("Your Favorite LIVE Streamer Monitor", main_layout, size=(450, 360), finalize=True,
                       icon='twitchmon.ico', border_depth=5, keep_on_top=True)  # scaling=True
    i = 0
    threads = []
    starting_app()
