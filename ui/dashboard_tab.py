import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models.visitor import VisitorModel
from models.checkin import VisitModel

class DashboardTab(QWidget):
    def __init__(self, user_session, parent=None):
        super().__init__(parent)
        self.user_session = user_session
        self.is_dark = True
        self.init_ui()
        self.refresh_counters()
        self.render_charts()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # 1. Page Title Header
        title_label = QLabel("Visitor Analytics Dashboard")
        title_label.setObjectName("TabTitle")
        self.main_layout.addWidget(title_label)

        # 2. Metric Cards Layout (Horizontal Row)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(15)
        self.main_layout.addLayout(self.cards_layout)

        # Initialize Metric Card widgets
        self.cards = {}
        metric_configs = [
            ('today_total', "Today's Total", "0", "Daily registration load", "#2ecc71"),
            ('active_visitors', "Active Visitors", "0", "Currently inside premises", "#ff2e93"),
            ('checked_out_today', "Checked Out Today", "0", "Completed visits", "#00ff66"),
            ('weekly_total', "Weekly Total", "0", "Rolling 7-day cumulative", "#3498db"),
            ('monthly_total', "Monthly Total", "0", "Rolling 30-day cumulative", "#9b59b6")
        ]

        for key, title, val, footer, accent in metric_configs:
            card_frame = QFrame()
            card_frame.setObjectName("MetricCard")
            card_layout = QVBoxLayout(card_frame)
            card_layout.setContentsMargins(15, 15, 15, 15)
            card_layout.setSpacing(4)
            
            # Title
            t_lbl = QLabel(title)
            t_lbl.setObjectName("MetricTitle")
            t_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            card_layout.addWidget(t_lbl)
            
            # Value
            v_lbl = QLabel(val)
            v_lbl.setObjectName("MetricValue")
            v_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
            v_lbl.setStyleSheet(f"color: {accent};")
            card_layout.addWidget(v_lbl)
            
            # Subtext
            f_lbl = QLabel(footer)
            f_lbl.setObjectName("MetricTrend")
            f_lbl.setFont(QFont("Segoe UI", 8))
            f_lbl.setStyleSheet("color: #7f8c8d;")
            card_layout.addWidget(f_lbl)

            self.cards_layout.addWidget(card_frame)
            self.cards[key] = v_lbl

        # 3. Chart Grid Layout (3 Charts: Line, Donut, Bar)
        self.chart_grid = QGridLayout()
        self.chart_grid.setSpacing(20)
        self.main_layout.addLayout(self.chart_grid)

        # Setup Matplotlib Figures
        self.line_fig = Figure(figsize=(5, 3), dpi=100)
        self.line_canvas = FigureCanvas(self.line_fig)
        self.chart_grid.addWidget(self._create_chart_card("Visitor Trends (Last 7 Days)", self.line_canvas), 0, 0)

        self.donut_fig = Figure(figsize=(5, 3), dpi=100)
        self.donut_canvas = FigureCanvas(self.donut_fig)
        self.chart_grid.addWidget(self._create_chart_card("Department Wise Traffic", self.donut_canvas), 0, 1)

        self.bar_fig = Figure(figsize=(10, 3.5), dpi=100)
        self.bar_canvas = FigureCanvas(self.bar_fig)
        self.chart_grid.addWidget(self._create_chart_card("Peak Visiting Hours", self.bar_canvas), 1, 0, 1, 2)

    def _create_chart_card(self, title, canvas):
        """Helper to wrap canvas in a beautiful card frame."""
        frame = QFrame()
        frame.setObjectName("MetricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl.setStyleSheet("color: #2ecc71; padding: 5px;")
        layout.addWidget(lbl)
        layout.addWidget(canvas)
        return frame

    def refresh_counters(self):
        """Fetch updated statistics from database and refresh cards."""
        try:
            stats = VisitModel.get_dashboard_counters()
            for key, val in stats.items():
                if key in self.cards:
                    self.cards[key].setText(str(val))
        except Exception as e:
            print(f"[Dashboard] Error refreshing counters: {e}")

    def render_charts(self):
        """Redraw all charts using database stats."""
        bg_color = '#181824' if self.is_dark else '#ffffff'
        text_color = '#ffffff' if self.is_dark else '#2c3e50'
        grid_color = '#2d2d3f' if self.is_dark else '#e2e8f0'

        # --- Chart 1: Line Graph (Trends) ---
        self.line_fig.clear()
        self.line_fig.patch.set_facecolor(bg_color)
        ax1 = self.line_fig.add_subplot(111)
        ax1.set_facecolor(bg_color)
        
        trend_data = VisitModel.get_weekly_trend_data()
        dates = [item['date'] for item in trend_data]
        counts = [item['count'] for item in trend_data]
        
        ax1.plot(dates, counts, marker='o', color='#2ecc71', linewidth=2.5, markersize=6)
        ax1.fill_between(dates, counts, color='#2ecc71', alpha=0.15)
        ax1.set_ylabel("Visitor Count", color=text_color, fontsize=9)
        ax1.tick_params(colors=text_color, labelsize=8)
        ax1.grid(True, color=grid_color, linestyle='--', alpha=0.5)
        ax1.spines['bottom'].set_color(grid_color)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color(grid_color)
        self.line_fig.tight_layout()
        self.line_canvas.draw()

        # --- Chart 2: Donut Chart (Department Wise) ---
        self.donut_fig.clear()
        self.donut_fig.patch.set_facecolor(bg_color)
        ax2 = self.donut_fig.add_subplot(111)
        ax2.set_facecolor(bg_color)
        
        dept_data = VisitModel.get_department_chart_data()
        if dept_data:
            labels = [row['department_name'] for row in dept_data]
            sizes = [row['count'] for row in dept_data]
            colors_list = ['#2ecc71', '#ff2e93', '#3498db', '#9b59b6', '#2ecc71', '#f1c40f']
            
            wedges, texts, autotexts = ax2.pie(
                sizes, labels=labels, autopct='%1.0f%%', startangle=90, pctdistance=0.8,
                colors=colors_list[:len(sizes)],
                textprops=dict(color=text_color, size=8)
            )
            # Add a white/dark circle in the center to make it a donut
            centre_circle = matplotlib.patches.Circle((0,0), 0.60, fc=bg_color)
            ax2.add_artist(centre_circle)
            
            # Format text colors
            for text in texts:
                text.set_color(text_color)
            for autotext in autotexts:
                autotext.set_color(text_color)
                autotext.set_fontweight('bold')
        else:
            # Draw placeholder if empty
            ax2.text(0.5, 0.5, 'No registration records yet', 
                     horizontalalignment='center', verticalalignment='center',
                     color=text_color)
            ax2.axis('off')
            
        self.donut_fig.tight_layout()
        self.donut_canvas.draw()

        # --- Chart 3: Bar Chart (Peak Hours) ---
        self.bar_fig.clear()
        self.bar_fig.patch.set_facecolor(bg_color)
        ax3 = self.bar_fig.add_subplot(111)
        ax3.set_facecolor(bg_color)
        
        hour_data = VisitModel.get_hourly_chart_data()
        hours = [item['hour'] for item in hour_data]
        counts3 = [item['count'] for item in hour_data]
        
        bars = ax3.bar(hours, counts3, color='#3498db', alpha=0.85, width=0.6, edgecolor='#2980b9', linewidth=1)
        
        # Highlight peak hours with different color
        if counts3 and max(counts3) > 0:
            max_val = max(counts3)
            for bar in bars:
                if bar.get_height() == max_val:
                    bar.set_facecolor('#2ecc71')
                    bar.set_edgecolor('#00939a')

        ax3.set_ylabel("Check-Ins", color=text_color, fontsize=9)
        ax3.tick_params(colors=text_color, labelsize=8)
        ax3.grid(True, axis='y', color=grid_color, linestyle='--', alpha=0.5)
        ax3.spines['bottom'].set_color(grid_color)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['left'].set_color(grid_color)
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax3.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', color=text_color, fontsize=8, fontweight='bold')
                            
        self.bar_fig.tight_layout()
        self.bar_canvas.draw()

    def set_chart_theme(self, dark=True):
        """Update chart backgrounds and line/text colors according to light/dark themes."""
        self.is_dark = dark
        self.render_charts()
