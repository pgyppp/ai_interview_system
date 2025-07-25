import wave
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def pcm_to_wav(pcm_path, output_path=None):
    """
    将PCM文件转换为WAV文件。
    Args:
        pcm_path (str): 输入的PCM文件路径。
        output_path (str, optional): 输出的WAV文件完整路径。
                                     如果未提供，则在PCM文件同级目录生成同名WAV文件。
    Returns:
        str: 转换后的WAV文件路径。
    Raises:
        FileNotFoundError: 如果PCM文件不存在。
        ValueError: 如果音频转换失败或文件不完整。
    """
    try:
        # 确保输入文件存在且大小合理
        if not os.path.exists(pcm_path):
            raise FileNotFoundError(f"PCM文件不存在: {pcm_path}")
            
        if output_path is None:
            # 如果 output_path 为 None，则在 pcm_path 的目录中生成 WAV 文件
            output_dir = os.path.dirname(pcm_path)
            # 使用 pcm_path 的文件名部分替换后缀为 .wav
            wav_path = os.path.join(output_dir, os.path.basename(pcm_path).replace('.pcm', '.wav'))
        else:
            wav_path = output_path
            target_dir = os.path.dirname(wav_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                logging.info(f"在 pcm_to_wav 中创建目标目录: {target_dir}")
        
        # 读取完整PCM数据
        with open(pcm_path, 'rb') as pcm_file:
            pcm_data = pcm_file.read()

        # 确保数据长度是2的倍数(16位PCM要求)
        if len(pcm_data) % 2 != 0:
            pcm_data = pcm_data[:-1]    # 移除最后一个不完整字节

        # 写入完整WAV文件
        # logging.debug(f"尝试写入WAV文件到: {wav_path}") # 调试日志
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setparams((
                1,               # 单声道
                2,               # 16位=2字节
                16000,           # 16kHz采样率
                0,               # 总帧数(自动计算)
                'NONE',          # 无压缩
                'not compressed'
            ))
            wav_file.writeframes(pcm_data)

        # 验证转换结果
        if os.path.getsize(wav_path) < len(pcm_data):
            raise ValueError("WAV文件转换不完整")

        logging.info(f"成功将 PCM '{pcm_path}' 转换为 WAV '{wav_path}'")
        return wav_path
        
    except Exception as e:
        # 清理不完整的文件
        # 确保在异常发生时，wav_path 已经被定义
        if 'wav_path' in locals() and os.path.exists(wav_path):
            os.remove(wav_path)
            logging.warning(f"由于转换失败，已清理不完整的WAV文件: {wav_path}")
        logging.error(f"音频转换失败: {e}", exc_info=True) # 打印详细堆栈
        raise ValueError(f"音频转换失败: {str(e)}")


def wav_to_pcm(wav_path, output_path=None):
    """
    WAV转PCM函数
    Args:
        wav_path (str): 输入的WAV文件路径。
        output_path (str, optional): 输出的PCM文件完整路径或目录。
                                     如果未提供，则在WAV文件同级目录生成同名PCM文件。
    Returns:
        str: 转换后的PCM文件路径。
    Raises:
        FileNotFoundError: 如果WAV文件不存在。
        ValueError: 如果音频转换失败，文件格式不支持或文件不完整。
    """
    try:
        # 确保输入文件存在且是有效的WAV文件
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV文件不存在: {wav_path}")
            
        # 设置输出路径
        # output_path 可以是完整的文件路径，也可以是目录
        if output_path and not os.path.isdir(output_path):
            # output_path 是完整的文件路径
            pcm_path = output_path
            output_dir = os.path.dirname(pcm_path)
        else:
            # output_path 是目录或 None，在 WAV 文件同级目录生成
            output_dir = output_path or os.path.dirname(wav_path)
            pcm_path = os.path.join(output_dir, os.path.basename(wav_path).replace('.wav', '.pcm'))
        
        # 确保输出目录存在
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"在 wav_to_pcm 中创建目录: {output_dir}")
        
        # 读取WAV文件
        with wave.open(wav_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
            
            # 验证是否为16位PCM格式 (1个通道, 2字节采样宽度, 16000采样率)
            # 根据您的 pcm_to_wav 函数，这里应该检查这些参数
            if params.nchannels != 1 or params.sampwidth != 2 or params.framerate != 16000:
                raise ValueError(f"仅支持单声道、16位、16kHz的WAV文件，当前文件参数：通道={params.nchannels}, 采样宽度={params.sampwidth}, 采样率={params.framerate}")
                
        # 写入PCM文件
        with open(pcm_path, 'wb') as pcm_file:
            pcm_file.write(frames)
            
        # 验证转换结果
        if os.path.getsize(pcm_path) != len(frames):
            raise ValueError("PCM文件转换不完整")
            
        logging.info(f"成功将 WAV '{wav_path}' 转换为 PCM '{pcm_path}'")
        return pcm_path
        
    except Exception as e:
        # 清理不完整的文件
        if 'pcm_path' in locals() and os.path.exists(pcm_path):
            os.remove(pcm_path)
            logging.warning(f"由于转换失败，已清理不完整的PCM文件: {pcm_path}")
        logging.error(f"音频转换失败: {e}", exc_info=True) # 打印详细堆栈
        raise ValueError(f"音频转换失败: {str(e)}")

