files = dir('vox1_dev_wav/**/*.wav');
disp(size(files));

L = length (files);

for i=1:L
    parts = strsplit(files(i).folder, '/');
    path = strcat(files(i).folder, '/', files(i).name);
    %disp(path);
    try
        [y,Fs] = audioread(path);

        [g,dg,a,ag] = iaif(y, Fs);

        %disp(g);
        %disp(size(iaif_result));
        %wlen = Fs / 4;

        %disp(length(iaif_result));
        % Magnitude spectrum
        hop = Fs / 10;
        nfft = 4096;
        windowsize = Fs/4;
        window = hanning(windowsize);
        magnitudeSpectrum = abs(stft(g, Fs, 'Window', window, 'OverlapLength', hop, 'FFTLength', nfft));


        fft_coefficients = v_rfft(magnitudeSpectrum);

        melFB = v_melbankm(30, length(magnitudeSpectrum), Fs);

        powerSpectrum = abs(fft_coefficients).^2;

        % Warp to mel
        warped_signal = melFB * powerSpectrum;
        % log
        z = log(warped_signal);
        % DCT
        glfcc = dct(z);
        relativePath = string(strjoin(parts(7:length(parts)),'/'));
        dirPath = strcat('Processed/', relativePath);
        pathToSave = strcat(dirPath, '/', files(i).name, '.txt');

        if ~exist(dirPath, 'dir')
           mkdir(dirPath)
        end
        writematrix(glfcc, pathToSave);
    catch
        fid = fopen('calculate_glfcc.log', 'a');
        fprintf(fid, 'Error processing file %s\n', path);
        fclose(fid);
    end
    
    if mod(i,100) == 0
        fprintf('Processed %.0f features\n', i);
    end
 
end


