using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using GroupDocs.Metadata;
using Ookii.Dialogs.Wpf;
using System.IO.Compression;
using Path = System.IO.Path;
using GroupDocs.Metadata.Standards.Exif;
using System.Globalization;
using System.Threading;
using iTextSharp.text;
using iTextSharp.text.pdf;
using System.Diagnostics;

namespace MangaToPdf
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private string directoryZipPath = "";

        public MainWindow()
        {
            InitializeComponent();
            CultureInfo ci = new CultureInfo("en-US");
            Thread.CurrentThread.CurrentCulture = ci;
            Thread.CurrentThread.CurrentUICulture = ci;
            PathTextBox.Text = "No path is chosen";
        }

        private void ChooseDirButton_Click(object sender, RoutedEventArgs e)
        {
            VistaFolderBrowserDialog folderBrowserDialog = new();
            folderBrowserDialog.Multiselect = false;
            string path = Directory.GetCurrentDirectory();
            directoryZipPath = path;
            folderBrowserDialog.SelectedPath = path;
            if (folderBrowserDialog.ShowDialog() is null ? false : true)
            {
                path = folderBrowserDialog.SelectedPath;
                directoryZipPath = path;
            } else
            {
                path = "No path is chosen";
            }
            PathTextBox.Text = path;
        }

        /// <summary>
        /// Removes extension in given string.
        /// Basically trims everything after last dot in string (the dot is also removed).
        /// </summary>
        /// <param name="name">String from which to remove extension part.</param>
        /// <returns>String without extension after last encountered dot (the dot is also removed).</returns>
        string GetTrimmedImageName(string name)
        {
            return name.Remove(name.LastIndexOf('.'));
        }

        /// <summary>
        /// Compares names of manga only considering chapters. Volume part is ignored.
        /// Used for sorting.
        /// </summary>
        int SimpleNameCompare(string name1, string name2)
        {
            float chapter1 = float.Parse(name1.Split()[^1]);
            float chapter2 = float.Parse(name2.Split()[^1]);
            if (chapter1 - chapter2 > 0)
                return 1;
            if (chapter1 - chapter2 < 0)
                return -1;
            return 0;
        }

        /// <summary>
        /// Compares names of manga considering both chapter and volume parts.
        /// Used for sorting.
        /// </summary>
        int NameCompare(string name1, string name2) {
            string[] name_as_args_arr = name1.Split();
            int start_index1 = Array.LastIndexOf(name_as_args_arr, "Том");
            if (start_index1 == -1)
            {
                throw new FormatException("Неправильный формат названия файла. Не было найдено слово \"Том\".");
            }
            float volume1 = float.Parse(name_as_args_arr[start_index1 + 1]);
            float chapter1 = float.Parse(name_as_args_arr[start_index1 + 3]);

            name_as_args_arr = name2.Split();
            int start_index2 = Array.LastIndexOf(name_as_args_arr, "Том");
            if (start_index1 == -1)
            {
                throw new FormatException("Неправильный формат названия файла. Не было найдено слово \"Том\".");
            }
            float volume2 = float.Parse(name_as_args_arr[start_index2 + 1]);
            float chapter2 = float.Parse(name_as_args_arr[start_index2 + 3]);

            if (volume1 != volume2)
                return (int)(volume1 - volume2);
            return (int)(chapter1 - chapter2);
        }

        /// <summary>
        /// Removes exif data from image.
        /// </summary>
        /// <param name="imagePath">Path to image.</param>
        void RemoveExif(string imagePath)
        {
            try
            {
                // Removing the EXIF data from an image.
                using (Metadata metadata = new Metadata(imagePath))
                {
                    IExif root = metadata.GetRootPackage() as IExif;
                    if (root != null)
                    {
                        root.ExifPackage = null;
                        metadata.Save(imagePath);
                    }
                }
            }
            catch (Exception e)
            {
                PrintLogInfo($"Could not remove exif data (metadata) from image. {e.Message}\n");
            }
        }

        /// <summary>
        /// Converts image format to JPG.
        /// </summary>
        /// <param name="image_path">Path to image.</param>
        void ConvertToJpg(string image_path)
        {
            string[] ALLOWED_IMAGE_EXTENSIONS = { ".png", ".jpeg", ".webp" };
            string extension = Path.GetExtension(image_path).ToLower();
            if (ALLOWED_IMAGE_EXTENSIONS.Contains(extension))
            {
                //Console.WriteLine(image_path);
                string name = Path.GetFileNameWithoutExtension(image_path);
                string path = Path.GetDirectoryName(image_path);

                System.Drawing.Image image = System.Drawing.Image.FromFile(image_path);

                image.Save(Path.Combine(path, $"{name}.jpg"), System.Drawing.Imaging.ImageFormat.Jpeg);
                image.Dispose();
                File.Delete(image_path);
            }
        }

        /*
         МЕСИВО С ПОПЫТКАМИ В КОНКАТЕНАЦИЮ ПДФ
         */

        void CreatePdfChapter(string[] imagePaths, string resultingPdfPath)
        {
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = @"..\..\..\py-env\Scripts\python.exe";
            start.Arguments = $"{@"..\..\..\converter.py"}";
            start.UseShellExecute = false;// Do not use OS shell
            start.CreateNoWindow = true; // We don't need new window
            start.RedirectStandardOutput = true;// Any output, generated by application will be redirected back
            start.RedirectStandardError = true; // Any error in standard output will be redirected back (for example exceptions)
            using (Process process = Process.Start(start))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    using (StreamWriter writer = process.StandardInput)
                    {
                        writer.WriteLine("n");
                        writer.WriteLine("");
                        writer.WriteLine("n");
                        writer.WriteLine("n");
                        string stderr = process.StandardError.ReadToEnd(); // Here are the exceptions from our Python script
                        string result = reader.ReadToEnd(); // Here is the result of StdOut(for example: print "test")
                    }
                }
            }
        }





        void PrintLogInfo(string message)
        {
            LogTextBox.Dispatcher.Invoke(() => {
                LogTextBox.AppendText(message);
                LogTextBox.ScrollToEnd();
            });
        }

        void ClearLog()
        {
            LogTextBox.Dispatcher.Invoke(() => {
                LogTextBox.Clear();
            });
        }

        /// <summary>
        /// Converts all zip files in folder to PDF files.
        /// Zip files must be in format that is usually used by MangaLib.
        /// Resulting PDFs are stored in "zipFolderPath/output".
        /// </summary>
        /// <param name="zipFolderPath">Path to folder that contains zip files downloaded from MangaLib.</param>
        private void ZipToPdf(string zipFolderPath)
        {
            Process process = new Process();
            PrintLogInfo("1\n");
            process.StartInfo.FileName = @"..\..\..\py-env\Scripts\python.exe";
            //process.StartInfo.Arguments = $"{@"..\..\..\converter.py"} z \"{zipFolderPath}\"";
            process.StartInfo.ArgumentList.Add(@"..\..\..\converter.py");
            process.StartInfo.ArgumentList.Add(@"z");
            process.StartInfo.ArgumentList.Add(zipFolderPath);
            process.StartInfo.CreateNoWindow = true; // We don't need new window
            process.StartInfo.UseShellExecute = false;// Do not use OS shell
            process.StartInfo.RedirectStandardOutput = true;// Any output, generated by application will be redirected back
            process.StartInfo.RedirectStandardError = true; // Any error in standard output will be redirected back (for example exceptions)
            //process.StartInfo.RedirectStandardInput = true;
            PrintLogInfo("2\n");

            process.OutputDataReceived += (s, e) => PrintLogInfo(e.Data);
            process.ErrorDataReceived += (s, e) => PrintLogInfo(e.Data);

            PrintLogInfo("3\n");
            process.Start();
            PrintLogInfo("4\n");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            //while (!process.StandardOutput.EndOfStream)
            //{
            //    PrintLogInfo(process.StandardOutput.ReadLine());
            //}
            process.WaitForExit();
            return;
            if (zipFolderPath == null)
            {
                throw new ArgumentException("Path to directory with zips was null.");
            }
            if (!Directory.Exists(zipFolderPath))
            {
                throw new DirectoryNotFoundException($"Directory does not exist. Given path: {zipFolderPath}.");
            }
            string outputFolderName = "output";
            string output_folder_path = Path.Combine(zipFolderPath, outputFolderName);

            // filter zips from all contents of the directory
            List<string> zipArchivesNames = new List<string>();
            foreach (var filepath in Directory.GetFiles(zipFolderPath))
            {
                if (System.IO.Path.GetExtension(filepath).Equals(".zip"))
                {
                    zipArchivesNames.Add(filepath.Remove(0, filepath.LastIndexOf('\\') + 1));
                }
            }
            PrintLogInfo("\nZIP archives: ------------------------------\n");
            zipArchivesNames.Sort(NameCompare);
            foreach (string s in zipArchivesNames)
                PrintLogInfo(s);

            // extract each zip archive as a folder into /output
            PrintLogInfo("\nExtraction: --------------------------------\n");
            string unzipped_folder_name = "unzipped";
            string output_unzip_folder_path = Path.Join(Path.Join(zipFolderPath, outputFolderName), unzipped_folder_name);
            if (!Directory.Exists(output_unzip_folder_path))
            {
                Directory.CreateDirectory(output_unzip_folder_path);
            }
            foreach (string filename in zipArchivesNames)
            {
                PrintLogInfo($"<-- extracting {filename} -->\n");
                ZipArchive zipArchive = ZipFile.Open(Path.Join(zipFolderPath, filename), ZipArchiveMode.Read);
                zipArchive.ExtractToDirectory(Path.Join(output_unzip_folder_path, filename[0..^18]), true);
                //ZipFile.ExtractToDirectory(Path.Join(zipFolderPath, filename), Path.Join(output_unzip_folder_path, filename[0..^18]));
                PrintLogInfo($"<-- extracted  {filename} -->\n");
            }

            // go through each extracted folder and collect all jpeg into a pdf file, which goes to /output
            PrintLogInfo("\nImage to pdf conversion: -------------------\n");
            string manga_name = "";
            Dictionary<string, List<string>> volume_dict = new Dictionary<string, List<string>>();
            if (Directory.Exists(output_unzip_folder_path))
            {
                List<string> image_directories = new List<string>(Directory.GetDirectories(output_unzip_folder_path).Select(filepath => filepath.Remove(0, filepath.LastIndexOf('\\') + 1)));
                image_directories.Sort(NameCompare);
                foreach (string directory_name in image_directories)
                {
                    string image_directory_path = Path.Join(output_unzip_folder_path, directory_name);
                    PrintLogInfo($"<-- converting {image_directory_path} -->\n");

                    string[] name_as_args_arr = directory_name.Split();
                    int start_index = Array.IndexOf(name_as_args_arr, "Том");
                    manga_name = string.Join(' ', name_as_args_arr[0..start_index]);
                    string volume = name_as_args_arr[start_index + 1];
                    if (!volume_dict.ContainsKey(volume))
                        volume_dict[volume] = new List<string>();
                    string chapter = name_as_args_arr[start_index + 3];

                    string[] correct_image_names = Directory.GetFiles(image_directory_path)
                                                            .Where(s => s.EndsWith(".jpeg") || s.EndsWith(".jpg") || s.EndsWith(".png") || s.EndsWith(".webp"))
                                                            .ToArray();
                    // convert all to jpg
                    foreach (string image_path in correct_image_names.Select(imageName => Path.Combine(image_directory_path, imageName)))
                    {
                        try
                        {
                            RemoveExif(image_path);
                            ConvertToJpg(image_path);
                            PrintLogInfo($"Image {image_path} was processed\n");
                        }
                        catch {
                            PrintLogInfo($"Could not convert to jpeg or remove exif data from {image_path}\n");
                        }
                    }
                    correct_image_names = Directory.GetFiles(image_directory_path)
                                                            .Where(s => s.EndsWith(".jpg"))
                                                            .Select(s => Path.GetFileNameWithoutExtension(s))
                                                            .ToArray();

                    List<string> sorted_image_names = correct_image_names.ToList();
                    sorted_image_names.Sort((string a, string b) => int.Parse(a).CompareTo(int.Parse(b)));
                    string[] sorted_image_paths = sorted_image_names.Select(s => Path.Combine(image_directory_path, s)).ToArray();
                    string pdf_chapter_path = Path.Join(output_folder_path, $"{manga_name} Том {volume} Глава {chapter}.pdf");

                    CreatePdfChapter(sorted_image_paths, pdf_chapter_path);

                    volume_dict[volume].Add(pdf_chapter_path);

                    PrintLogInfo($"<-- converted {image_directory_path} -->\n");
                }
            }
        }

        private void ConvertToPdfButton_Click(object sender, RoutedEventArgs e)
        {
            // TODO: REMEMBER TO STORE PROCESSES AND KILL THEM IF APP HAS BEEN CLOSED
            new Thread(() => ZipToPdf(directoryZipPath)).Start();
        }
    }
}
