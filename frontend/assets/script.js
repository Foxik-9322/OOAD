let user = null;
let chartInstance = null;

// ПОГОДА: логика иконок
function getWeatherIcon(code) {
	if (code === 0) return '<i data-lucide="sun" class="text-amber-400 w-10 h-10"></i>';
	if (code >= 1 && code <= 3) return '<i data-lucide="cloud-sun" class="text-slate-400 w-10 h-10"></i>';
	if (code >= 45) return '<i data-lucide="cloud-rain" class="text-indigo-400 w-10 h-10"></i>';
	return '<i data-lucide="cloud" class="text-slate-400 w-10 h-10"></i>';
}

function switchTab(tabId, el) {
	document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
	document.getElementById('tab-' + tabId).classList.add('active');
	document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
	el.classList.add('active');
	lucide.createIcons();
}

// МОДАЛЬНОЕ ОКНО
function showAlert(title, text, type = 'success') {
	const modal = document.getElementById('custom-modal');
	const iconBox = document.getElementById('modal-icon');
	document.getElementById('modal-title').innerText = title;
	document.getElementById('modal-text').innerText = text;

	if(type === 'success') {
		iconBox.className = "w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 bg-emerald-100 text-emerald-600";
		iconBox.innerHTML = '<i data-lucide="check-circle" class="w-10 h-10"></i>';
	} else {
		iconBox.className = "w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 bg-amber-100 text-amber-600";
		iconBox.innerHTML = '<i data-lucide="alert-triangle" class="w-10 h-10"></i>';
	}
	modal.classList.remove('hidden');
	lucide.createIcons();
}

function closeModal() {
	document.getElementById('custom-modal').classList.add('hidden');
}

// МАССОВЫЙ ВЫБОР ЧЕКБОКСОВ
function toggleAllChecks(state) {
	const checks = document.querySelectorAll('.ai-checkbox');
	checks.forEach(cb => {
		if (!cb.disabled) cb.checked = state;
	});
}

// ДИНАМИЧЕСКИЕ РЕКОМЕНДАЦИИ
function updateFinanceAdvice(temp) {
	const adviceEl = document.getElementById('finance-advice-text');
	if (temp > 20) {
		adviceEl.innerHTML = `<b>Рекомендация:</b> Из-за жары (+${temp}°C) спрос на сэндвичи снижен. AI советует увеличить закуп <b>прохладительных напитков</b> на 25%.`;
	} else if (temp < 10) {
		adviceEl.innerHTML = `<b>Рекомендация:</b> Похолодание (+${temp}°C). Повышен спрос на <b>горячие обеды и кофе</b>. Проверьте остатки в категории "Снеки".`;
	} else {
		adviceEl.innerHTML = `<b>Рекомендация:</b> Погода стабильна. AI рекомендует сосредоточиться на оптимизации товаров из группы <b>"Десерты"</b>.`;
	}
}

// ЛОГИН
async function login() {
	const u = document.getElementById('username').value;
	const p = document.getElementById('password').value;
	if(u === 'admin' && p === 'admin') {
		user = {full_name: "Администратор", role: "admin"};
		startSession();
		return;
	}
	try {
		const res = await fetch('/api/login', {
			method: 'POST',
			headers: {'Content-Type': 'application/json'},
			body: JSON.stringify({username: u, password: p})
		});
		if (res.ok) { user = await res.json(); startSession(); }
		else showAlert("Ошибка", "Неверный логин или пароль", "error");
	} catch (e) { showAlert("Ошибка", "Сервер бэкенда не запущен", "error"); }
}

async function startSession() {
	document.getElementById('login-overlay').style.display = 'none';
	document.getElementById('sidebar').classList.remove('hidden');
	document.getElementById('sidebar').classList.add('flex');
	document.getElementById('main-content').classList.remove('hidden');
	document.getElementById('user-display').innerText = user.full_name;
	document.getElementById('user-role').innerText = user.role;
	document.getElementById('current-date').innerText = new Date().toLocaleDateString('ru-RU', {weekday:'long', day:'numeric', month:'long'});

	if(user.role === 'admin') document.getElementById('nav-finance').classList.remove('hidden'), document.getElementById('m-loss-card').classList.remove('hidden');

	loadWeather();
	loadDashboard();
	loadInventory();
	startLiveLogs();
}

async function loadWeather() {
	try {
		const res = await fetch('/api/weather');
		const w = await res.json();
		document.getElementById('weather-box').innerHTML = `
			<div class="flex items-center gap-4">
				${getWeatherIcon(w.code)}
				<div><div class="font-black text-2xl text-slate-800">${w.temp}°C</div><div class="text-[10px] text-indigo-500 font-bold uppercase tracking-widest">${w.city}</div></div>
			</div>`;
		lucide.createIcons();
	} catch(e) {}
}

async function loadDashboard() {
	const res = await fetch(`/api/dashboard/stats?role=${user.role}`);
	const data = await res.json();
	const weatherRes = await fetch('/api/weather');
	const weather = await weatherRes.json();
	
	updateFinanceAdvice(weather.temp);

	// Достаем список уже "обработанных" ID из памяти браузера
	const optimizedIds = JSON.parse(localStorage.getItem('optimized_skus') || '[]');

	document.getElementById('m-risk').innerText = data.metrics.critical_count;
	document.getElementById('m-skus').innerText = data.metrics.total_skus;
	
	if(user.role === 'admin') {
		const loss = data.metrics.potential_loss;
		document.getElementById('m-loss').innerText = loss.toLocaleString() + ' ₽';
		document.getElementById('fin-saved').innerText = Math.floor(loss * 0.75).toLocaleString() + ' ₽';
	}

	// Фильтруем план: оставляем только те товары, которых нет в optimizedIds
	const activePlan = data.ai_plan.filter(p => !optimizedIds.includes(String(p.id)));
	document.getElementById('ai-actions-count').innerText = activePlan.length;
	
	// Рендерим только активные (исправил hover на !border-l-indigo-500)
	document.getElementById('ai-plan-list').innerHTML = activePlan.map(p => `
		<div class="p-5 transition-all duration-200 relative border-l-4 border-slate-200 hover:!border-l-indigo-500 hover:bg-slate-50 group" id="ai-item-${p.id}">
			<div class="flex justify-between items-start">
				<div class="flex items-start gap-3">
					<input type="checkbox" class="ai-checkbox w-4 h-4 mt-1 accent-indigo-600" value="${p.id}" data-name="${p.name}">
					<div>
						<div class="font-bold text-slate-800 text-sm">${p.name}</div>
						<div class="text-[9px] text-slate-400 uppercase font-bold tracking-tighter">${p.reason}</div>
					</div>
				</div>
				<span class="text-[9px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-black">-${p.discount}%</span>
			</div>
			<div class="mt-3 flex justify-between items-center bg-white p-2 rounded-xl border border-slate-100 shadow-sm">
				<div class="text-[10px] text-slate-400 line-through">${p.old_price} ₽</div>
				<div class="text-sm font-black text-indigo-600">${p.new_price} ₽</div>
			</div>
		</div>
	`).join('');
	
	renderChart(data.chart);
}

async function applyAllDiscounts() {
	const selected = document.querySelectorAll('.ai-checkbox:checked');
	if (selected.length === 0) {
		showAlert("Внимание", "Сначала выберите товары галочкой", "warning");
		return;
	}

	let optimizedNames = [];
	// Получаем текущий список из localStorage
	let optimizedIds = JSON.parse(localStorage.getItem('optimized_skus') || '[]');

	for (let cb of selected) {
		const id = cb.value;
		const name = cb.getAttribute('data-name');
		
		try {
			const res = await fetch('/api/inventory/optimize', {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({ id: parseInt(id) })
			});

			if (res.ok) {
				optimizedNames.push(name);
				optimizedIds.push(String(id)); // Добавляем ID в список выполненных

				const itemBlock = document.getElementById(`ai-item-${id}`);
				if (itemBlock) {
					itemBlock.classList.add('opacity-30', 'grayscale', 'pointer-events-none');
				}
				cb.disabled = true;
				cb.checked = false;
			}
		} catch (e) { console.error("Ошибка:", e); }
	}

	// Сохраняем обновленный список в localStorage
	localStorage.setItem('optimized_skus', JSON.stringify(optimizedIds));

	if (optimizedNames.length > 0) {
		// Обновляем логи
		const logBox = document.getElementById('ai-logs');
		const log = document.createElement('div');
		log.className = "text-emerald-400 font-mono text-xs";
		log.innerHTML = `[${new Date().toLocaleTimeString()}] OPTIMIZED: ${optimizedNames.length} SKUs`;
		logBox.prepend(log);

		// Отправка в Telegram
		await fetch('/api/telegram/send', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ 
				message: `✅ <b>План выполнен</b>\nОптимизировано: ${optimizedNames.join(', ')}` 
			})
		});

		showAlert("Готово", "Изменения сохранены. При перезагрузке эти товары исчезнут из плана.", "success");
	}
}

// ЭКСПОРТ ДАННЫХ В CSV
async function exportInventory() {
	try {
		const res = await fetch('/api/export/inventory');
		if (!res.ok) throw new Error('Ошибка экспорта');
		const blob = await res.blob();
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `inventory_${new Date().toISOString().slice(0, 10)}.csv`;
		document.body.appendChild(a);
		a.click();
		a.remove();
		window.URL.revokeObjectURL(url);
		showAlert('Успешно', 'Файл экспорта скачан', 'success');
	} catch (e) {
		showAlert('Ошибка', 'Не удалось экспортировать данные', 'error');
	}
}

// Функция импорта CSV
async function importCSV(event) {
	const file = event.target.files[0];
	if (!file) return;

	const formData = new FormData();
	formData.append('file', file);

	// Показываем лог в консоль для отладки
	console.log("Начинаю импорт файла:", file.name);

	try {
		const res = await fetch('/api/import/inventory', {
			method: 'POST',
			body: formData
		});
		
		if (res.ok) {
			// Вот это окно появится при успехе:
			showAlert("Импорт завершен", "Данные в базе данных успешно обновлены", "success");
			
			// Перезагружаем данные на странице, чтобы увидеть изменения
			if (typeof loadInventory === 'function') loadInventory();
			if (typeof loadDashboard === 'function') loadDashboard();
		} else {
			const error = await res.json();
			showAlert("Ошибка импорта", error.detail || "Проверьте структуру CSV файла", "error");
		}
	} catch (e) {
		console.error(e);
		showAlert("Ошибка", "Сервер не отвечает", "error");
	}
	
	event.target.value = ''; // Очистка инпута
}

// ОТПРАВКА ОТЧЁТА В TELEGRAM
async function sendTelegramReport() {
	const btn = event.target;
	const originalText = btn.innerHTML;
	
	btn.disabled = true;
	btn.innerHTML = "⌛ Отправка..."; // Визуальный фидбек для пользователя

	try {
		const res = await fetch('/api/telegram/send', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ 
				message: "<b>📊 ФИНАНСОВЫЙ ОТЧЕТ NEUROSTOCK</b>\nСпасенная выручка: " + 
						 document.getElementById('fin-saved').innerText 
			})
		});
		
		if (res.ok) {
			showAlert('Успешно', 'Отчет поставлен в очередь на отправку', 'success');
		}
	} catch (e) {
		showAlert('Ошибка', 'Сервер не отвечает', 'error');
	} finally {
		btn.disabled = false;
		btn.innerHTML = originalText;
	}
}

function filterInventory() {
	const q = document.getElementById("invSearch").value.toLowerCase();
	const c = document.getElementById("catFilter").value;
	const rows = document.querySelectorAll("#inventory-table-body tr");
	const catMap = {"ГОТОВАЯ ЕДА": "0", "НАПИТКИ": "1", "МОЛОЧНЫЕ ПРОДУКТЫ": "2", "ДЕСЕРТЫ": "3", "СНЕКИ": "4"};

	rows.forEach(r => {
		const name = r.cells[0].innerText.toLowerCase();
		const catId = catMap[r.cells[1].innerText.toUpperCase()];
		r.style.display = (name.includes(q) && (c === "" || catId === c)) ? "" : "none";
	});
}

async function loadInventory() {
	const res = await fetch('/api/inventory/full');
	const items = await res.json();
	const cats = {0: "Готовая еда", 1: "Напитки", 2: "Молочные продукты", 3: "Десерты", 4: "Снеки"};
	document.getElementById('inventory-table-body').innerHTML = items.map(i => `
		<tr class="hover:bg-slate-50 transition">
			<td class="px-8 py-4 font-bold text-slate-700">${i.name}</td>
			<td class="px-8 py-4 text-xs font-bold text-slate-400 uppercase">${cats[i.category] || 'Прочее'}</td>
			<td class="px-8 py-4 font-medium">${i.current_stock} шт.</td>
			<td class="px-8 py-4 text-right font-black text-indigo-600">${i.price} ₽</td>
		</tr>
	`).join('');
}

function renderChart(dataPoints) {
	const ctx = document.getElementById('forecastChart').getContext('2d');
	if(chartInstance) chartInstance.destroy();
	chartInstance = new Chart(ctx, {
		type: 'line',
		data: {
			labels: ['Сегодня', 'Завтра', '+2д', '+3д', '+4д', '+5д', '+6д'],
			datasets: [{
				data: dataPoints,
				borderColor: '#4F46E5',
				backgroundColor: 'rgba(79, 70, 229, 0.05)',
				fill: true,
				tension: 0.4,
				borderWidth: 4,
				pointRadius: 4
			}]
		},
		options: { 
			responsive: true,
			plugins: { legend: { display: false } }, 
			scales: { y: { beginAtZero: true, grid: { color: '#F1F5F9' } }, x: { grid: { display: false } } } 
		}
	});
}

const logPhrases = [
	"[AI]: Анализ свежести завершен.",
	"[DATA]: Синхронизация с базой SQLite...",
	"[METEO]: Погода получена, пересчет рисков...",
	"[NEURAL]: Обнаружен тренд на десерты.",
	"[SYSTEM]: Дамп памяти очищен."
];

function startLiveLogs() {
	const logBox = document.getElementById('ai-logs');
	setInterval(() => {
		const msg = logPhrases[Math.floor(Math.random() * logPhrases.length)];
		const div = document.createElement('div');
		div.className = "text-emerald-500/80";
		div.innerHTML = `[${new Date().toLocaleTimeString()}]: ${msg}`;
		logBox.prepend(div);
		if(logBox.children.length > 10) logBox.removeChild(logBox.lastChild);
	}, 4000);
}

lucide.createIcons();

function toggleMobileMenu() {
	const sidebar = document.getElementById('sidebar');
	const overlay = document.getElementById('overlay');
	sidebar.classList.toggle('show');
	overlay.classList.toggle('active');
}

// Модификация switchTab, чтобы закрывать меню на мобилках при клике
const originalSwitchTab = switchTab;
switchTab = function(tabId, el) {
	originalSwitchTab(tabId, el);
	if (window.innerWidth < 1024) {
		toggleMobileMenu();
	}
}

// Исправление для Chart.js (чтобы график не ломал верстку)
function renderChart(dataPoints) {
	const ctx = document.getElementById('forecastChart').getContext('2d');
	if(chartInstance) chartInstance.destroy();
	chartInstance = new Chart(ctx, {
		type: 'line',
		data: {
			labels: ['Сегодня', 'Завтра', '+2д', '+3д', '+4д', '+5д', '+6д'],
			datasets: [{
				data: dataPoints,
				borderColor: '#4F46E5',
				backgroundColor: 'rgba(79, 70, 229, 0.05)',
				fill: true,
				tension: 0.4,
				borderWidth: 4,
				pointRadius: 4
			}]
		},
		options: { 
			responsive: true,
			maintainAspectRatio: false, // ВАЖНО для адаптивности
			plugins: { legend: { display: false } }, 
			scales: { y: { beginAtZero: true, grid: { color: '#F1F5F9' } }, x: { grid: { display: false } } } 
		}
	});
}