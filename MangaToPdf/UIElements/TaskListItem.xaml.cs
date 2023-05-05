using System.Windows.Controls;

namespace MangaToPdf.UIElements
{
    /// <summary>
    ///     Interaction logic for TaskListItem.xaml
    /// </summary>
    public partial class TaskListItem : UserControl
    {
        public TaskListItem()
        {
            InitializeComponent();
        }

        public void PrintLogInfo(string message = "")
        {
            if (message == null) return;
            if (message.StartsWith("[PROGRESS]"))
            {
                if (ProgressBar == null) return;
                Dispatcher.Invoke(() => { ProgressBar.Value = int.Parse(message.Split()[1]); });
            }
            else
            {
                if (LogTextBox == null) return;
                LogTextBox.Dispatcher.Invoke(() =>
                {
                    LogTextBox.AppendText($"{message}\n");
                    LogTextBox.ScrollToEnd();
                });
            }
        }

        public void ClearLog()
        {
            LogTextBox.Dispatcher.Invoke(() => { LogTextBox.Clear(); });
        }
    }
}