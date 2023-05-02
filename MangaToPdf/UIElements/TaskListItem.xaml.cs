using System;
using System.Collections.Generic;
using System.Diagnostics;
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

namespace MangaToPdf.UIElements
{
    /// <summary>
    /// Interaction logic for TaskListItem.xaml
    /// </summary>
    public partial class TaskListItem : UserControl
    {
        public TaskListItem()
        {
            InitializeComponent();
        }

        public void PrintLogInfo(string message = "")
        {
            LogTextBox.Dispatcher.Invoke(() =>
            {
                LogTextBox.AppendText($"{message}\n");
                LogTextBox.ScrollToEnd();
            });
        }

        public void ClearLog()
        {
            LogTextBox.Dispatcher.Invoke(() =>
            {
                LogTextBox.Clear();
            });
        }
    }
}
