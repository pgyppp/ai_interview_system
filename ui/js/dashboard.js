// // 日期显示
// document.addEventListener('DOMContentLoaded', function() {
// 	const now = new Date();
// 	const options = {
// 		year: 'numeric',
// 		month: 'long',
// 		day: 'numeric'
// 	};
// 	const formattedDate = now.toLocaleDateString('zh-CN', options);
// 	document.getElementById('current-date').textContent = formattedDate;
// });
 // 导航栏滚动效果
        window.addEventListener('scroll', function() {
            const nav = document.getElementById('main-nav');
            if (window.scrollY > 10) {
                nav.classList.add('shadow-elevation-2');
                nav.classList.remove('shadow-elevation-1');
                nav.classList.add('bg-white/95');
                nav.classList.remove('bg-glass');
            } else {
                nav.classList.remove('shadow-elevation-2');
                nav.classList.add('shadow-elevation-1');
                nav.classList.remove('bg-white/95');
                nav.classList.add('bg-glass');
            }
        });

        // 滚动显示动画
        function checkScroll() {
            const elements = document.querySelectorAll('.scroll-reveal');
            elements.forEach((element, index) => {
                const elementTop = element.getBoundingClientRect().top;
                const elementVisible = 150;
                if (elementTop < window.innerHeight - elementVisible) {
                    setTimeout(() => {
                        element.classList.add('active');
                    }, index * 100);
                }
            });
        }

        window.addEventListener('scroll', checkScroll);
        window.addEventListener('load', checkScroll);

        // 数字增长动画
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                const stats = [
                    { id: 'efficiency-improvement', value: 78 },
                    { id: 'time-reduction', value: 65 },
                    { id: 'quality-improvement', value: 42 },
                    { id: 'cost-reduction', value: 35 }
                ];
                
                stats.forEach((stat, index) => {
                    setTimeout(() => {
                        const element = document.getElementById(stat.id);
                        let current = 0;
                        const target = stat.value;
                        const duration = 1800;
                        const step = target / (duration / 16);
                        
                        const updateNumber = () => {
                            current += step;
                            if (current < target) {
                                element.textContent = Math.min(Math.round(current), target) + '%';
                                requestAnimationFrame(updateNumber);
                            } else {
                                element.textContent = target + '%';
                                element.classList.add('animate-pulse');
                                setTimeout(() => element.classList.remove('animate-pulse'), 1000);
                            }
                        };
                        
                        updateNumber();
                    }, index * 300);
                });

                // 初始化图表
                const ctx = document.getElementById('recruitmentChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                        datasets: [
                            {
                                label: '传统招聘周期(天)',
                                data: [35, 32, 30, 28, 25, 22],
                                borderColor: '#4E5969',
                                backgroundColor: 'rgba(78, 89, 105, 0.1)',
                                tension: 0.4,
                                fill: true
                            },
                            {
                                label: 'AI系统招聘周期(天)',
                                data: [18, 15, 12, 10, 8, 7],
                                borderColor: '#165DFF',
                                backgroundColor: 'rgba(22, 93, 255, 0.1)',
                                tension: 0.4,
                                fill: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        },
                        animation: {
                            duration: 2000,
                            easing: 'easeOutQuart'
                        }
                    }
                });
            }, 1000);
        });

        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    const footerHeight = document.querySelector('footer').offsetHeight;
                    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - footerHeight;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });