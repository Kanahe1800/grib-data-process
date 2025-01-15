import pygrib
import pandas as pd



def selectFileAndOpen(year, month, day, hour, minute, duration):
    """
    :param int year: データの収得を開始する年
    :param int month: データの収得を開始する月
    :param int day: データの収得を開始する日付
    :param int hour: データの収得を開始する時間
    :param int minute: データの収得を開始する分
    :param int duration: データを収得する期間(分数)
    """
    try:
        #print(duration)
        max_numeber_of_required_file = 0
        if(duration > 0):
            max_numeber_of_required_file = duration // 60 + 1
            print(max_numeber_of_required_file)
            if(hour + max_numeber_of_required_file > 23):
                required_day = (hour + max_numeber_of_required_file) // 24
                print((hour + max_numeber_of_required_file) // 24)
                print(max_numeber_of_required_file // 24)
        file_name = "XR183_User11_" + str(year)
        if month < 10:
            file_name += "0" + str(month)
        else:
            file_name += str(month)
        if day < 10:
            file_name += "0" + str(day)
        else:
            file_name += str(day)
        #hourにminuteの組み合わせは全てテスト済み
        if hour < 10:
            if(minute != 0):
                file_name += "_0" + str(hour) + "00.grb2"
            else:
                file_name += "_0" + str(hour - 1) + "00.grb2"
        else:
            if(minute != 0):
                file_name += "_" + str(hour) + "00.grb2"
            else:
                file_name += "_" + str(hour - 1) + "00.grb2"
        gpv_file = pygrib.open(file_name)
        print(file_name)
        max_numeber_of_required_file = duration // 60 + 1
        u_messages = gpv_file.select(parameterName="u-component of wind")
        v_messages = gpv_file.select(parameterName="v-component of wind")
        if(minute > 0 and minute <= 59):
            current_message_index = minute // 10 - 1
        elif (minute == 0):
            current_message_index = len(u_messages) - 1
        else:
            print("minute invalid")
            return "minute invalid"
        current_u_message = u_messages[current_message_index]
        current_v_message = v_messages[current_message_index]
        #print(len(u_messages))
        print(current_u_message.validDate, current_u_message.latlons()[0][0])
        #print(current_v_message.validDate, current_v_message.latlons())
        gpv_file.close()
    except OSError:
        print("file not found")
        return "file not found"
    except Exception as e:
        print("Unknown Error" + e)
        return "Unknown Error" + e
    
selectFileAndOpen(2024, 11, 8, 17, 10, 2890)
#df = pd.DataFrame()