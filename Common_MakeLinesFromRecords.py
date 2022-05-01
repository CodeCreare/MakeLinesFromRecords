# coding: UTF-8
import io
import re
import os
import datetime
import logging
logger = logging.getLogger()




def Execute(func, log_level=logging.DEBUG, sleep_sec=10, sleep_str='DEFAULT', log_open_when_end=False, sleep_output=True):
	InitLogging(log_level, log_open_when_end)
	flag_exception	= False
	try:
		func()
	except Exception as e:
		import traceback
		logger.error(e)
		logger.error(traceback.format_exc())
		flag_exception	= True

	if not flag_exception:
		Sleep(sleep_sec, sleep_str, sleep_output)


def Sleep(sec, str_info='', output=True):
	if sec == 0:
		return
	import time
	if str_info == 'DEFAULT':
		str_out	= '__SEC__秒Sleepして、終了します'
	elif str_info == '':
		str_out	= 'sleep __SEC__ sec'
	else:
		str_out	= str_info
	
	if '__SEC__' in str_out:
		str_out	= str_out.replace('__SEC__', str(sec))

	global s_open_when_end
	if s_open_when_end:
		OpenLogAtTerminate()

	if output:
		logger.info(str_out)
		for sec_now in range(sec):
			print(str(sec_now) + '、', end='', flush=True)
			time.sleep(1)
		print('')

	else:
		logger.debug(str_out)
		time.sleep(sec)



def GetZenkakuLength(str_zen):
	import unicodedata
	len	= 0
	str_check	= GetValueStr(str_zen, False)
	for c in str_check:
		if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
			len += 2
		else:
			len += 1
	return len



def SetDefaultIfNone(value, default_value):
	if value == None:
		return default_value
	return value



def GetOs():
	if os.name == 'nt':
		return 'Windows'
	elif os.name == 'posix':
		return 'Linux'
	else:
		logger.critical('os.name==%s', os.name)



def OpenFiles(files):
	str_os	= GetOs()
	if str_os == 'Linux':
		return

	for file in files:
		if file != '' and (not os.path.exists(file) and not re.match('http', file)):
			logger.error(file + 'は存在しません！')
			continue

		if re.match('.+xlsx*', file):
			OpenWithExcel(file)
		elif re.match('http', file):
			OpenWithChrome(file)
		elif file != '' and file != '-':
			OpenWithExplorer(file)


def OpenWithExplorer(file):
	if not ':' in file:
		dir	= os.getcwd()
		file	= os.path.join(dir, file)

	import subprocess
	subprocess.run('explorer {}'.format(file))


def OpenWithChrome(file):
	exes = [
		r'C:\Program Files\Google\Chrome\Application\chrome.exe',
		r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
	]
	for exe in exes:
		if os.path.exists(exe):
			str_exe	= exe + ' "' + file + '"'
			import subprocess
			subprocess.Popen(str_exe)


def OpenWithExcel(file):
	exes = [
		r'C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE',
		r'C:\Program Files (x86)\Microsoft Office\Office14\EXCEL.EXE',
	]
	file	= file.replace('/', '\\')
	for exe in exes:
		if os.path.exists(exe):
			str_exe	= exe + ' "' + file + '"'
			import subprocess
			subprocess.Popen(str_exe)



def GetCurrentTimeStr():
	import pytz
	tm_now	= datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
	str_jst	= tm_now.strftime('%Y%m%d_%H%M%S')
	return str_jst


def GetCaller():
	import inspect
	stacks		= inspect.stack()
	if len(stacks) < 4 or stacks[3].function == '_run_code':
		file_caller	= stacks[2].filename
		result		= False
	else:
		file_caller	= stacks[3].filename
		result		= True

	tmp, fname_caller	= os.path.split(file_caller)
	fname_caller		= fname_caller.replace('.py', '')
	return fname_caller, result


s_file_detaillog	= ''
s_file_errorlog		= ''
s_open_when_end		= False
def InitLogging(log_level, open_when_end=False):
	global s_file_detaillog
	global s_file_errorlog
	global s_open_when_end

	caller, result		= GetCaller()
	s_open_when_end		= open_when_end
	handler_format		= logging.Formatter('%(asctime)s [%(levelname)-7s] %(filename)-12s:%(lineno)4d [%(funcName)s] %(message)s', datefmt='%m/%d %H:%M:%S')

	# Debug - ファイル出力(詳細)
	s_file_detaillog	= os.path.join(caller + '_DetailLog_' + GetCurrentTimeStr() + '.txt')
	handler_debug 		= logging.FileHandler(s_file_detaillog, 'w', encoding='utf-8')
	handler_debug.setLevel(logging.DEBUG)
	handler_debug.setFormatter(handler_format)
	logger.addHandler(handler_debug)
	# Info - 標準出力
	handler_info 		= logging.StreamHandler()
	handler_info.setLevel(logging.INFO)
	handler_info.setFormatter(handler_format)
	logger.addHandler(handler_info)
	# Error - ファイル出力(エラー)
	s_file_errorlog		= os.path.join(caller + '_ErrorLog_' + GetCurrentTimeStr() + '.txt')
	handler_error 		= logging.FileHandler(s_file_errorlog, 'w', encoding='utf-8')
	handler_error.setLevel(logging.WARNING)
	handler_error.setFormatter(handler_format)
	logger.addHandler(handler_error)
	# Critical - 強制終了
	logger.addHandler(HandlerCriticalLog(logging.CRITICAL))
	
	logger.setLevel(log_level)													# ログレベル設定
	import atexit
	atexit.register(CB_AtTerminate)												# プログラム終了時処理
	if result == False:
		logger.error('%s is launched not from Execute', caller)


class HandlerCriticalLog(logging.StreamHandler):
	def emit(self, record):
		if logging.CRITICAL <= record.levelno:
			global s_open_when_end
			s_open_when_end	= True
			import inspect
			for s1 in inspect.stack():
				tmp, fname	= os.path.split(s1.filename)
				logger.error('[%s] %d %s', fname, s1.lineno, s1.function)
			import sys
			sys.exit(1)


def CB_AtTerminate():
	global s_file_errorlog
	OpenLogAtTerminate()
	logging.shutdown()
	if os.path.getsize(s_file_errorlog) == 0:
		os.remove(s_file_errorlog)


def OpenLogAtTerminate():
	global s_open_when_end
	if s_open_when_end:
		OpenLogFile()
		s_open_when_end	= False


def OpenLogFile():
	global s_file_detaillog
	global s_file_errorlog
	if os.path.getsize(s_file_errorlog) == 0:
		OpenFiles([s_file_detaillog])
	else:
		OpenFiles([s_file_detaillog, s_file_errorlog])



def ConvLines2LinesStr(lines):
	str_lines	= ''
	for line in lines:
		str_lines	+= line + '\n'
	str_lines	= str_lines[0 : len(str_lines) - 1]
	return str_lines



def GetPos(layout, zenkaku):
	if zenkaku:
		pos	= layout[3]
	else:
		pos	= layout[2]
	return pos


def IsThisRightest(layouts, l, zenkaku):
	for l2 in range(l+1, len(layouts)):
		layout_next	= layouts[l2]
		pos_next	= GetPos(layout_next, zenkaku)
		if pos_next != -1:
			key	= layout_next[0]
			if key == 'RIGHT_EDGE':
				return True
			else:
				return False

	logger.critical('l=%d, layouts=%s', l, layouts)


def IsLastPos(layouts, l, zenkaku):
	is_last	= True
	for l2 in range(l+1, len(layouts)):
		layout_next	= layouts[l2]
		pos_next	= GetPos(layout_next, zenkaku)
		if pos_next != -1 and layout_next[0] != 'RIGHT_EDGE':
			is_last	= False

	return is_last


def GetCopyKeysMultiTitle(keys_org, cutpolicy='CUTPLICY_TOP'):
	if keys_org == None or len(keys_org) == 0:
		keys_new	= []
	else:
		import copy
		keys_new	= copy.deepcopy(keys_org)
		if cutpolicy == 'CUTPLICY_TOP':
			del keys_new[0]
		elif cutpolicy == 'CUTPLICY_LAST':
			del keys_new[-1]
		elif cutpolicy == 'CUTPLICY_NONE':
			pass
		else:
			logger.critical('policy invalid')

	return keys_new


def GetNextValidPos(layouts, l, zenkaku, keys_multi_title=None):
	keys_ignore_overlap	= GetCopyKeysMultiTitle(keys_multi_title, cutpolicy='CUTPLICY_NONE')

	for l2 in range(l+1, len(layouts)):
		layout_next	= layouts[l2]
		if layout_next[0] in keys_ignore_overlap:
			continue

		pos_next	= GetPos(layout_next, zenkaku)
		if pos_next == -1:
			continue

		if zenkaku and pos_next % 2 == 1:
			logger.critical('全角時のレイアウトは偶数にしてください, l=%d, layouts=%s', l, layouts)

		return pos_next

	logger.critical('l=%d, layouts=%s', l, layouts)


def MakeTitleLineFromLayouts(layouts, zenkaku):
	record			= MakeTitleRecord(layouts)
	line, rn, fn	= Make1LineFromRecord(record, layouts, zenkaku)
	return line


def MakeTitleRecord(layouts):
	record	= {}
	for layout in layouts:
		key			= layout[0]
		title		= layout[1]
		record[key]	= title
	return record


def GetPrimitiveLen(zenkaku):
	if zenkaku:
		return 2
	else:
		return 1


def GetSpace(zenkaku):
	if zenkaku:
		return '　'
	else:
		return ' '


def GetBar(zenkaku):
	if zenkaku:
		return '－'
	else:
		return '--'


def SeparateStr(str_org, len_forthis, is_right, is_rightest, zenkaku):
	str_front	= ''
	str_back	= ''
	len_write	= len_forthis
	if not is_rightest:
		len_write	-= GetPrimitiveLen(zenkaku)

	for i in range(len(str_org)):
		str_new	= str_org[0:i+1]
		len_new	= GetZenkakuLength(str_new)
		if len_new <= len_write:
			str_front	= str_new
			str_back	= str_org[i+1:]

		elif str_front == '' and str_back == '':
			logger.critical('１文字もおけない状況です。 i=%d, str_org=%s(type=%s), len_write=%d, str_new=%s(len=%d), str_front=%s, str_back=%s, zenkaku=%d', i, str_org, type(str_org), len_write, str_new, len_new, str_front, str_back, zenkaku)

	len_value	= GetZenkakuLength(str_front)
	len_tofill	= len_forthis - len_value - GetPrimitiveLen(zenkaku)
	if is_rightest and not is_right:
		len_tofill	= 0

	str_fill	= ''
	for d in range(0, len_tofill, GetPrimitiveLen(zenkaku)):
		str_fill	+= GetSpace(zenkaku)

	str_space		= GetSpace(zenkaku)
	if is_rightest:
		str_space	= ''
	if is_right:
		str_front	= str_fill + str_front + str_space
	else:
		str_front	= str_front + str_fill + str_space

	return str_front, str_back


def GetValueStr(value, zeroval_space):
	if type(value) == dict:
		value	= '<dict>'
	if type(value) == list:
		value	= '<list>'
	elif type(value) == int:
		if zeroval_space and value == 0:
			value	= ' '
		else:
			value	= str(value)

	return str(value)


def GetLayoutInfos(layout, zenkaku):
	key			= layout[0]
	pos			= GetPos(layout, zenkaku)
	is_right	= False
	if 4 < len(layout):
		is_right	= layout[4]
	maxtate		= 1
	if 5 < len(layout):
		maxtate		= layout[5]

	return key, pos, is_right, maxtate


def GetValue(record, key, zeroval_space, str_when_notexist, zenkaku):
	if key in record:
		value	= GetValueStr(record[key], zeroval_space)
	else:
		value	= str_when_notexist
	if zenkaku:
		value	= ConvHankaku2Zenkaku(value)
	return value


def Make1LineFromRecord(record, layouts, zenkaku, zeroval_space=True, str_when_notexist='', row=1000, keys_multi_title=None):
	line		= ''
	record_next	= {}
	flag_next	= False
	for l in range(len(layouts)):
		key, pos, is_right, maxtate	= GetLayoutInfos(layouts[l], zenkaku)
		if l == 0 and pos != 0:
			for d in range(0, pos, GetPrimitiveLen(zenkaku)):
				line	+= GetSpace(zenkaku)

		if key == 'RIGHT_EDGE' or pos == -1:
			logger_extra_debug('row=%d, l=%d, zenkaku=%d, key=%s, pos=%d, is_right=%d, maxtate=%d', row, l, zenkaku, key, pos, is_right, maxtate)
			continue

		record_next[key]	= ''
		value		= GetValue(record, key, zeroval_space, str_when_notexist, zenkaku)
		pos_next	= GetNextValidPos(layouts, l, zenkaku, keys_multi_title)
		is_rightest	= IsThisRightest(layouts, l, zenkaku)
		len_forthis	= pos_next - pos

		str_front, str_back	= SeparateStr(value, len_forthis, is_right, is_rightest, zenkaku)
		line				+= str_front
		if row < maxtate - 1 and str_back != '':
			record_next[key]	= str_back
			flag_next			= True

		logger_extra_debug('row=%d, l=%d, zenkaku=%d, key=%s, pos=%d, is_right=%d, maxtate=%d, value=%s, pos_next=%d, str_front=%s, str_back=%s', row, l, zenkaku, key, pos, is_right, maxtate, value, pos_next, str_front, str_back)

	return line, record_next, flag_next


def ValidCheckLayouts(layouts, zenkaku, keys_multi_title):
	keys_ignore_overlap	= GetCopyKeysMultiTitle(keys_multi_title, cutpolicy='CUTPLICY_LAST')

	len_layouts	= len(layouts)
	is_firstpos	= True
	for l in range(len(layouts)):
		layout	= layouts[l]
		if len(layout) < 4:
			logger.critical('1行分のレイアウト情報でパラメタ不足(4つ未満), layout=%s', layout)

		elif l == len_layouts - 1:
			key		= layout[0]
			if key != 'RIGHT_EDGE':
				logger.critical('最後のレイアウト情報がRIGHT_EDGEでない, layout=%s', layout)

		else:
			pos_now		= GetPos(layout, zenkaku)
			pos_next	= GetNextValidPos(layouts, l, zenkaku)
			if pos_next - pos_now < GetPrimitiveLen(zenkaku) * 2:
				if not layout[0] in keys_ignore_overlap:
					logger.critical('1文字も置けない, pos_now=%d, pos_next=%d, layout=%s, zenkaku=%d, layouts=\n%s', pos_now, pos_next, layout, zenkaku, layouts)

			if is_firstpos:
				is_firstpos	= False
				if (pos_now != -1 and pos_now != 0) or (pos_now == -1 and pos_next != 0):
					if not layout[0] in keys_ignore_overlap:
						logger.critical('最初のpos指定が0でない、pos_now=%d, pos_next=%d, layouts=%s, zenkaku=%d, layouts=\n%s', pos_now, pos_next, layout, zenkaku, layouts)


def MakeTitleLayouts(layouts, maxtate_title):
	import copy
	layouts_title	= copy.deepcopy(layouts)
	for layout in layouts_title:
		if len(layout) < 5:
			logger.critical('通る？')
			layout	+= [False, 1]
		elif len(layout) < 6:
			logger.critical('通る？')
			layout	+= [1]

		if len(layout) < 6:
			logger.critical('layout=%s', layout)
		layout[5]	= maxtate_title

#	logger.debug('layouts_title=%s', layouts_title)
	return layouts_title


def GetMaxLineLength(lines_title, lines_data):
	len_max_d	= 0
	if len(lines_data) != 0:
		len_max_d	= max([GetZenkakuLength(line) for line in lines_data])
	len_max_t	= max([GetZenkakuLength(line) for line in lines_title])
	len_max		= max(len_max_d, len_max_t)
	return len_max


def MakeOutputLines(zenkaku, lines_title, lines_data, output_1block=False):
	len_max		= GetMaxLineLength(lines_title, lines_data)
	line_bar	= GetBar(zenkaku) * int((len_max + 1) / 2)
#	line_bar	= '0--34567891--34567892--34567893--34567894--34567895--34567896--34567897--34567898--34567899--3456789h--3456789'
	lines		= lines_title
	lines		+= [line_bar]
	lines		+= lines_data
	if output_1block:
		return ConvLines2LinesStr(lines)

	return lines


def GetThisLayoutPos(layouts, l, maxlengths):
	if l == 0:
		return 0
	layout	= layouts[l - 1]
	if layout[0] not in maxlengths:
		logger.error('layout=%s, maxlengths=%s', layout, maxlengths)

	return layout[2] + maxlengths[layout[0]] + 1


def GetMaxLengths(records, options):
	maxlengths		= {}
	for record in records:
		for key in record:
			if not key in maxlengths:
				maxlengths[key] = 0
			lenkey	= GetZenkakuLength(key)
			if maxlengths[key] < lenkey:
				maxlengths[key] = lenkey

			lenval	= GetZenkakuLength(record[key])
			if maxlengths[key] < lenval:
				maxlengths[key] = lenval

	if 'maxlengths' in options:
		for key in options['maxlengths']:
			maxlength_option	= options['maxlengths'][key]
			if key not in maxlengths:
				logger.debug('key[%s] of %s not in records', key, options['maxlengths'])
			elif maxlength_option < maxlengths[key]:
				maxlengths[key]	= maxlength_option

	return maxlengths


def SetLayouts_Maxlengths(layouts, options, records):
	maxlengths	= GetMaxLengths(records, options)
	for l in range(len(layouts)):
		layout	= layouts[l]
		pos		= GetThisLayoutPos(layouts, l, maxlengths)
		if len(layout) <= 2:
			layout	+= [pos, pos]
		else:
			layout[2]	= pos
			layout[3]	= pos

	return layouts


def SetLayouts_AlignRights(layouts, options):
	if 'align_rights' not in options:
		return layouts

	for layout in layouts:
		for key in options['align_rights']:
			if key == layout[0]:
				if len(layout) < 5:
					layout.append(True)
				else:
					layout[4]	= True

	return layouts


def SetLayouts_Showitems(layouts, options, records):
	keys_in_records	= []
	for record in records:
		for key in record:
			keys_in_records.append(key)
	keys_in_records	= list(set(keys_in_records))
	keys_layouts	= [l[0] for l in layouts]
	keys_added		= []
	if 'showitems' in options:
		for key_show in options['showitems']:
			if key_show in keys_layouts:
				continue
			if key_show in keys_in_records:
				layouts.insert(len(layouts) - 1, [key_show, key_show])
				keys_added.append(key_show)
#				logger.debug('key_show(%s) is added to layouts', key_show)
			else:
				logger.debug('key_show(%s) is in showitems, but not records', key_show)

		keys_layouts			= [l[0] for l in layouts]
		keys_only_inrecords		= list(set(keys_in_records) - set(keys_layouts))
		logger.debug('keys(%s) are in records but not shown in the log', keys_only_inrecords)
		logger.debug('keys(%s) were added to layouts', keys_added)
	else:
		for key_show in keys_in_records:
			if key_show in keys_layouts:
				continue
			layouts.insert(len(layouts) - 1, [key_show, key_show])

	return layouts


def SetLayouts_ShowOrder(layouts, options):
	if 'showorder' not in options:
		return layouts

	keys_order		= options['showorder']
	layouts_new		= []
	for key in keys_order:
		keys_layouts	= [l[0] for l in layouts]
		if key in keys_layouts:
			index	= keys_layouts.index(key)
			layout	= layouts.pop(index)
			layouts_new.append(layout)

	for layout in layouts:
		layouts_new.append(layout)

	return layouts_new


def SetLayouts_ShowOrder_New(layouts, options):
	if 'showorder' not in options:
		return layouts

	keys_order		= options['showorder']
	keys_layouts	= [l[0] for l in layouts]
	layouts_new		= []
	for key in keys_order:
		if key not in keys_layouts:
			layouts_new.append([key, key])

	for layout in layouts:
		layouts_new.append(layout)

	logger_extra_debug('layouts=\n%s', ConvData2Json(layouts))
	logger_extra_debug('layouts_new=\n%s', ConvData2Json(layouts_new))
	return layouts_new


def SetLayouts_Finally(layouts):
	for layout in layouts:
		if len(layout) < 5:
			layout.append(False)
		if len(layout) < 6:
			layout.append(1)

	return layouts


def MakeLayoutsIfSrcExist(layouts, layouts_src, records):
#	if layouts == None and layouts_src == None:
#		logger.debug('layouts == None and layouts_src == None')
	if layouts != None and layouts_src != None:
		logger.critical('layouts != None and layouts_src != None')
	elif layouts != None:
		return layouts

	layouts_src	= SetDefaultIfNone(layouts_src, {})
	layouts		= []
	layouts.append(['RIGHT_EDGE', '', 300, 300])
	layouts		= SetLayouts_Showitems(layouts, layouts_src, records)
	layouts		= SetLayouts_ShowOrder(layouts, layouts_src)
	layouts		= SetLayouts_Maxlengths(layouts, layouts_src, records)
	layouts		= SetLayouts_AlignRights(layouts, layouts_src)
	layouts		= SetLayouts_Finally(layouts)

	logger_extra_info('MakeLayoutsIfSrcExist layouts=\n%s', MakeLinesFromArrays(layouts))

	return layouts


def AddLayoutsIfMultiTitleKeysExist(layouts, str_multi_title, keys_multi_title, indent_multi_title):
	if keys_multi_title == None and str_multi_title == '':
		return layouts

	pos_layout	= 0
	for key in keys_multi_title:
		pos		= pos_layout * indent_multi_title
		layout	= [key, 'DUMMY', pos, pos, False, 1]
		if pos_layout == 0:
			layout[1]	= str_multi_title
		else:
			layout[1]	= ''

		layouts[pos_layout:pos_layout]	= [layout]
		pos_layout	+= 1

#	logger.info('layouts=\n%s', MakeIndentJsonStr(layouts))
	return layouts


def MakeLinesFromRecord(record, layouts, keys_multi_title, zenkaku, zeroval_space, str_when_notexist):
	lines			= []
	records_tmp		= [record]
	for t in range(10):
		record	= records_tmp[t]
		line, record_next, flag_next	= Make1LineFromRecord(record, layouts, zenkaku, zeroval_space, str_when_notexist, t, keys_multi_title)
		lines.append(line)
		if flag_next:
			records_tmp.append(record_next)
		else:
			break
	return lines


# layouts		: 
#						key				title		半角時pos	全角時ops	右寄せ	縦行数
#					[	'customer',		'ユーザ',	0,			0,			False,	1		],

# layouts_src	: align_rights / showorder / showitems / maxlengths
#					showitemsを指定したら、表示項目指定＆順序指定になるので、showorderは指定不要。
def MakeLinesFromRecords(records, layouts=None, layouts_src=None, zenkaku=False, zeroval_space=True, str_when_notexist='', maxtate_title=1, output_1block=False, str_multi_title='', keys_multi_title=None, indent_multi_title=2):
	layouts				= MakeLayoutsIfSrcExist(layouts, layouts_src, records)
	layouts				= AddLayoutsIfMultiTitleKeysExist(layouts, str_multi_title, keys_multi_title, indent_multi_title)
	keys_multi_title	= SetDefaultIfNone(keys_multi_title, [])
	ValidCheckLayouts(layouts, zenkaku, keys_multi_title)
	layouts_title		= MakeTitleLayouts(layouts, maxtate_title)
	record_title		= MakeTitleRecord(layouts)
	layouts_title		= MakeLayouts_Only1TitleKey(layouts_title, keys_multi_title, record_title)
	lines_title			= MakeLinesFromRecord(record_title, layouts_title, keys_multi_title, zenkaku, zeroval_space, str_when_notexist)
	lines_data			= []
	for record in records:
		layouts_this	= MakeLayouts_Only1TitleKey(layouts, keys_multi_title, record)
		lines_data		+= MakeLinesFromRecord(record, layouts_this, keys_multi_title, zenkaku, zeroval_space, str_when_notexist)

	lines	= MakeOutputLines(zenkaku, lines_title, lines_data, output_1block)
	return lines


def MakeLinesFromArrays(arrays):
	lines	= []
	for array in arrays:
		line	= ''
		for value in array:
			line	+= str(value) + ' '

		lines.append(line)

	return ConvLines2LinesStr(lines)


def MakeLayouts_Only1TitleKey(layouts, keys_title, record):
	layouts_exist	= []
	title_exist		= False
	for layout in layouts:
		key		= layout[0]
		if key == 'RIGHT_EDGE' or key not in keys_title:
			layouts_exist.append(layout)
		else:
			if key in record and title_exist == False:
				layouts_exist.append(layout)
				title_exist		= True

	return layouts_exist



s_flag_extralog_MakeLinesFromRecords	= False
def SetExtraLog_MakeLinesFromRecords(flag):
	global s_flag_extralog_MakeLinesFromRecords
	s_flag_extralog_MakeLinesFromRecords	= flag

def logger_extra_debug(*args):
	global s_flag_extralog_MakeLinesFromRecords
	if not s_flag_extralog_MakeLinesFromRecords:
		return
	logger.debug(*args)


def logger_extra_info(*args):
	global s_flag_extralog_MakeLinesFromRecords
	if not s_flag_extralog_MakeLinesFromRecords:
		return
	logger.info(*args)



def Debug_MakeLinesFromRecords():
	members = [{'Name': 'Alice XXX', 'Age': 40, 'Points': 80, 'Extra':'extra info is so long that you may need to set max length to show'}, 
				{'Name': 'Bob YYY', 'Age': 20, 'Points': 120},
				{'Name': 'Charlie ZZZ', 'Age': 30, 'Points': 70}]

	logger.info('disp1=\n%s\n', MakeLinesFromRecords(members, layouts_src={'showorder' : ['Name', 'Age', 'Points']}, output_1block=True))
	logger.info('dips2=\n%s\n', MakeLinesFromRecords(members, layouts_src={'showorder' : ['Name', 'Age', 'Points'], 'align_rights' : ['Points']}, output_1block=True))
	logger.info('disp3=\n%s\n', MakeLinesFromRecords(members, layouts_src={'showorder' : ['Name', 'Age', 'Points'], 'maxlengths': {'Extra':15}}, output_1block=True))
	logger.info('disp4=\n%s\n', MakeLinesFromRecords(members, layouts_src={'showorder' : ['Name', 'Age', 'Points'], 'showitems': ['Name', 'Age', 'Points']}, output_1block=True))


def Debug():
	Debug_MakeLinesFromRecords()



if __name__ == '__main__':
	Execute(Debug, sleep_sec=0)



