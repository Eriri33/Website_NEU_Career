
const $ = selector => document.querySelector(selector);

const api = async url => {
  const response = await fetch(url, { credentials: 'same-origin' });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.message || 'Không thể tải dữ liệu.');
  }

  return data;
};

const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  "'": '&#39;',
  '"': '&quot;'
}[c]));

const params = new URLSearchParams(location.search);
const firstJobId = params.get('job1');

const jobTypes = {
  internship: 'Thực tập',
  full_time: 'Toàn thời gian',
  part_time: 'Bán thời gian',
  contract: 'Hợp đồng'
};

const saturdayLabels = {
  off: 'Nghỉ thứ Bảy',
  working: 'Làm thứ Bảy',
  negotiable: 'Thỏa thuận',
  unknown: 'Chưa rõ'
};

let firstJob = null;
let comparedJobs = null;
let comparisonMap = null;
let comparisonMarkers = [];

/* ===== LOAD JOB COMPARISON OPTIONS ===== */

async function loadComparisonOptions() {
  try {
    $('#compareButton').disabled = true;

    if (!firstJobId) {
      $('#compareMessage').textContent =
        'Bạn chưa chọn công việc đầu tiên. Hãy quay lại trang tìm việc.';

      $('#secondJob').disabled = true;
      return;
    }

    // Lấy thông tin công việc thứ nhất
    firstJob = await api(
      '/api/jobs/' + encodeURIComponent(firstJobId)
    );

    // Lấy danh sách công việc và cây danh mục
    const [jobs, categories] = await Promise.all([
      api('/api/jobs'),
      api('/api/categories/')
    ]);

    // Tạo bản đồ danh mục theo ID
    const categoryMap = new Map();

    // API categories trả về cây nested, tự bổ sung parent_id
    function flattenCategories(items, parentId = null) {
      items.forEach(category => {
        const normalizedCategory = {
          ...category,
          parent_id: parentId
        };

        categoryMap.set(
          String(category.id),
          normalizedCategory
        );

        if (category.children?.length) {
          flattenCategories(category.children, category.id);
        }
      });
    }

    flattenCategories(categories);

    // Chuẩn hóa tiếng Việt để so sánh tên ngành
    function normalizeText(value) {
      return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd')
        .replace(/Đ/g, 'D')
        .toLowerCase()
        .trim();
    }

    // Xác định danh mục cấp 1 của công việc đang chọn
    let currentCategory = categoryMap.get(
      String(firstJob.category_id)
    );

    while (currentCategory?.parent_id != null) {
      currentCategory = categoryMap.get(
        String(currentCategory.parent_id)
      );
    }

    // Lấy đường dẫn danh mục từ cấp hiện tại lên cấp gốc
    const selectedCategoryPath = [];
    let selectedNode = categoryMap.get(
      String(firstJob.category_id)
    );

    while (selectedNode) {
      selectedCategoryPath.push(selectedNode.name);

      selectedNode = selectedNode.parent_id != null
        ? categoryMap.get(String(selectedNode.parent_id))
        : null;
    }

    // Tạo từ khóa ngành nghề liên quan
    const relatedTerms = selectedCategoryPath
      .flatMap(name => name.split(/[-–,]/))
      .map(name => normalizeText(name))
      .filter(name => name.length >= 4);

    // Lọc công việc cùng nhóm ngành hoặc có tên liên quan
    const availableJobs = jobs.filter(job => {
      // Không cho phép so sánh một công việc với chính nó
      if (String(job.id) === String(firstJobId)) {
        return false;
      }

      // Xác định nhóm ngành cấp 1 của công việc ứng viên
      let node = categoryMap.get(String(job.category_id));

      while (node?.parent_id != null) {
        node = categoryMap.get(String(node.parent_id));
      }

      // Kiểm tra cùng nhóm ngành cấp 1
      const sameRoot = currentCategory && node &&
        String(node.id) === String(currentCategory.id);

      // Kiểm tra tên công việc và tên danh mục
      const candidateText = normalizeText(
        `${job.title} ${job.category_name || ''}`
      );

      const relatedByName = relatedTerms.some(term =>
        candidateText.includes(term)
      );

      return sameRoot || relatedByName;
    });

    // Sắp xếp tên công việc theo A-Z
    availableJobs.sort((a, b) =>
      (a.title || '').localeCompare(b.title || '', 'vi')
    );

    // Hiển thị danh sách công việc thứ hai
    $('#secondJob').innerHTML = availableJobs.length
      ? '<option value="">-- Chọn công việc muốn so sánh --</option>' +
        availableJobs.map(job =>
          `<option value="${esc(job.id)}">${esc(job.title)} — ${esc(job.company_name)}</option>`
        ).join('')
      : '<option value="">Chưa có công việc cùng hoặc liên quan ngành</option>';

    // Hiển thị thông báo
    $('#compareMessage').textContent = availableJobs.length
      ? `Công việc thứ nhất: ${firstJob.title} | Tìm thấy ${availableJobs.length} công việc cùng hoặc liên quan ngành nghề.`
      : 'Chưa tìm thấy công việc cùng hoặc liên quan ngành nghề.';

    // Bật/tắt nút so sánh
    $('#compareButton').disabled = availableJobs.length === 0;
    $('#secondJob').disabled = availableJobs.length === 0;

  } catch (error) {
    $('#compareMessage').textContent = error.message;
    $('#secondJob').disabled = true;
    $('#compareButton').disabled = true;
  }
}

/* ===== DISPLAY DEFAULT VALUES ===== */

function valueOrDefault(value, fallback = 'Chưa cập nhật') {
  return value ? esc(value) : fallback;
}

/* ===== RENDER COMPARISON TABLE ===== */

function renderComparison(job1, job2) {
  const rows = [
    ['Doanh nghiệp', job1.company_name, job2.company_name],

    [
      'Mức lương',
      job1.salary_text || 'Thỏa thuận',
      job2.salary_text || 'Thỏa thuận'
    ],

    ['Địa điểm', job1.location, job2.location],

    [
      'Loại công việc',
      jobTypes[job1.job_type] || job1.job_type,
      jobTypes[job2.job_type] || job2.job_type
    ],

    ['Ngành nghề', job1.category_name, job2.category_name],

    [
      'Ngành học phù hợp',
      job1.major_required || 'Không giới hạn',
      job2.major_required || 'Không giới hạn'
    ],

    ['Kỹ năng yêu cầu', job1.skills_required, job2.skills_required],

    [
      'Lịch làm thứ Bảy',
      saturdayLabels[job1.saturday_policy] || 'Chưa rõ',
      saturdayLabels[job2.saturday_policy] || 'Chưa rõ'
    ],

    [
      'Hạn ứng tuyển',
      job1.deadline || 'Không giới hạn',
      job2.deadline || 'Không giới hạn'
    ],

    ['Mô tả công việc', job1.description, job2.description]
  ];

  $('#jobOneTitle').textContent = job1.title;
  $('#jobTwoTitle').textContent = job2.title;

  $('#compareBody').innerHTML = rows.map(
    ([label, value1, value2]) => `
      <tr>
        <th>${esc(label)}</th>
        <td>${valueOrDefault(value1)}</td>
        <td>${valueOrDefault(value2)}</td>
      </tr>
    `
  ).join('');

  $('#compareResult').hidden = false;
}

/* ===== COMPARE SELECTED JOBS ===== */

async function compareSelectedJobs() {
  const secondJobId = $('#secondJob').value;
  if (!firstJob) {
    $('#compareMessage').textContent =
      'Không tìm thấy công việc thứ nhất.';

    return;
  }
  if (!secondJobId) {
    $('#compareMessage').textContent =
      'Vui lòng chọn công việc thứ hai.';

    return;
  }
  try {
    $('#compareButton').disabled = true;

    const secondJob = await api(
      '/api/jobs/' + encodeURIComponent(secondJobId)
    );

    comparedJobs = [firstJob, secondJob];

    renderComparison(firstJob, secondJob);

    $('#compareMessage').textContent =
      'Đã tải bảng so sánh thành công.';

  } catch (error) {
    $('#compareMessage').textContent = error.message;

  } finally {
    $('#compareButton').disabled = false;
  }
}

/* ===== ADDRESS AUTOCOMPLETE ===== */

let selectedHomeLocation = null;
let addressSearchTimer = null;
let addressSearchController = null;
let addressSearchVersion = 0;

const homeAddressInput = $('#homeAddress');
const addressSuggestions = $('#addressSuggestions');
const calculateDistanceButton = $('#calculateDistanceButton');
const locationMessage = $('#locationMessage');


function hideAddressSuggestions() {
  addressSuggestions.hidden = true;
  addressSuggestions.innerHTML = '';
}


function showAddressMessage(message) {
  addressSuggestions.innerHTML = '';

  const item = document.createElement('button');
  item.type = 'button';
  item.className = 'address-suggestion';
  item.disabled = true;
  item.textContent = message;

  addressSuggestions.appendChild(item);
  addressSuggestions.hidden = false;
}


function selectHomeLocation(location) {
  selectedHomeLocation = location;

  homeAddressInput.value = location.label;

  hideAddressSuggestions();

  calculateDistanceButton.disabled = false;

  locationMessage.textContent =
    'Đã chọn địa chỉ. Bạn có thể tiếp tục tính khoảng cách.';
}


function renderAddressSuggestions(results) {
  addressSuggestions.innerHTML = '';

  if (!results.length) {
    showAddressMessage(
      'Không tìm thấy địa chỉ phù hợp tại Việt Nam. Vui lòng thử lại.'
    );
    return;
  }

  results.forEach(result => {
    const button = document.createElement('button');

    button.type = 'button';
    button.className = 'address-suggestion';
    button.textContent = result.label;

    button.addEventListener('click', () => {
      selectHomeLocation(result);
    });

    addressSuggestions.appendChild(button);
  });

  addressSuggestions.hidden = false;
}


async function searchHomeAddress(query) {
  if (addressSearchController) {
    addressSearchController.abort();
  }

  const controller = new AbortController();
  addressSearchController = controller;

  const version = ++addressSearchVersion;

  try {
    const response = await fetch(
      '/api/locations/search?q=' + encodeURIComponent(query),
      {
        credentials: 'same-origin',
        signal: controller.signal
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.message || 'Không thể tìm kiếm địa chỉ.'
      );
    }

    // Bỏ qua kết quả của truy vấn cũ
    if (version !== addressSearchVersion) {
      return;
    }

    renderAddressSuggestions(data.results || []);

  } catch (error) {
    if (error.name === 'AbortError') {
      return;
    }

    if (version === addressSearchVersion) {
      showAddressMessage(
        'Dịch vụ tìm kiếm địa chỉ đang gặp sự cố. Vui lòng thử lại.'
      );
    }
  }
}


homeAddressInput.addEventListener('input', () => {
  const query = homeAddressInput.value.trim();

  // Nhập lại địa chỉ thì phải chọn lại gợi ý
  selectedHomeLocation = null;
  calculateDistanceButton.disabled = true;

  locationMessage.textContent =
    'Vui lòng chọn một địa chỉ trong danh sách gợi ý.';

  clearTimeout(addressSearchTimer);

  if (addressSearchController) {
    addressSearchController.abort();
  }

  if (query.length < 3) {
    hideAddressSuggestions();
    locationMessage.textContent =
      'Nhập ít nhất 3 ký tự để tìm địa chỉ.';
    return;
  }

  showAddressMessage('Đang tìm địa chỉ...');

  // Chờ người dùng ngừng nhập khoảng 350ms
  addressSearchTimer = setTimeout(() => {
    searchHomeAddress(query);
  }, 350);
});


// Ẩn gợi ý khi nhấn ra ngoài vùng nhập địa chỉ
document.addEventListener('click', event => {
  if (
    !event.target.closest('.address-autocomplete')
  ) {
    hideAddressSuggestions();
  }
});


/* ===== GEOCODE COMPANY LOCATIONS ===== */

async function geocodeCompanyLocation(location) {
  if (!location || !location.trim()) {
    throw new Error('Công việc chưa có thông tin địa điểm.');
  }

  const query = location.trim() + ', Việt Nam';

  const data = await api(
    '/api/locations/search?q=' + encodeURIComponent(query)
  );

  if (!data.results || data.results.length === 0) {
    throw new Error(
      `Không tìm thấy tọa độ cho địa điểm: ${location}`
    );
  }

  const result = data.results[0];

  return {
    latitude: Number(result.latitude),
    longitude: Number(result.longitude),
    label: result.label,
    originalLocation: location,
    approximate: location.split(',').length < 2
  };
}


/* ===== HAVERSINE DISTANCE ===== */

function calculateDistance(lat1, lon1, lat2, lon2) {
  const earthRadius = 6371;

  const toRadians = degree => degree * Math.PI / 180;

  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
    Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) ** 2;

  const c = 2 * Math.atan2(
    Math.sqrt(a),
    Math.sqrt(1 - a)
  );

  return earthRadius * c;
}


function formatDistance(distance) {
  if (distance < 1) {
    return `${Math.round(distance * 1000)} m`;
  }

  return `${distance.toFixed(1).replace('.', ',')} km`;
}


/* ===== CALCULATE DISTANCES ===== */

calculateDistanceButton.addEventListener('click', async () => {
  if (!selectedHomeLocation) {
    locationMessage.textContent =
      'Vui lòng chọn địa chỉ từ danh sách gợi ý trước.';
    return;
  }

  if (!comparedJobs) {
    locationMessage.textContent =
      'Vui lòng so sánh hai công việc trước.';
    return;
  }

  try {
    calculateDistanceButton.disabled = true;
    calculateDistanceButton.textContent = 'Đang tính...';

    locationMessage.textContent =
      'Đang xác định vị trí hai doanh nghiệp...';

    $('#distanceResult').hidden = true;
    $('#showMapButton').hidden = true;
    $('#comparisonMap').hidden = true;

    // Tìm tọa độ hai doanh nghiệp
    const [companyOne, companyTwo] = await Promise.all([
      geocodeCompanyLocation(comparedJobs[0].location),
      geocodeCompanyLocation(comparedJobs[1].location)
    ]);

    const home = {
      latitude: selectedHomeLocation.latitude,
      longitude: selectedHomeLocation.longitude,
      label: selectedHomeLocation.label
    };

    // Tính khoảng cách đường chim bay
    const distanceOne = calculateDistance(
      home.latitude,
      home.longitude,
      companyOne.latitude,
      companyOne.longitude
    );

    const distanceTwo = calculateDistance(
      home.latitude,
      home.longitude,
      companyTwo.latitude,
      companyTwo.longitude
    );

    // Hiển thị kết quả
    $('#distanceJobOneName').textContent =
      comparedJobs[0].title;

    $('#distanceJobTwoName').textContent =
      comparedJobs[1].title;

    $('#distanceJobOne').textContent =
      formatDistance(distanceOne);

    $('#distanceJobTwo').textContent =
      formatDistance(distanceTwo);

    $('#distanceResult').hidden = false;
    $('#showMapButton').hidden = false;

    // Lưu dữ liệu tọa độ để vẽ bản đồ
    window.jobComparisonLocations = {
      home,
      companyOne,
      companyTwo
    };

    let message =
      'Khoảng cách được tính theo đường chim bay, không phải quãng đường di chuyển thực tế.';

    if (companyOne.approximate || companyTwo.approximate) {
      message +=
        ' Địa điểm chỉ có thông tin cấp tỉnh/khu vực nên kết quả tương ứng chỉ mang tính ước tính.';
    }

    locationMessage.textContent = message;

  } catch (error) {
    locationMessage.textContent = error.message;

  } finally {
    calculateDistanceButton.disabled = false;
    calculateDistanceButton.textContent = 'Tính khoảng cách';
  }
});


/* ===== DISPLAY LEAFLET MAP ===== */

$('#showMapButton').addEventListener('click', () => {
  const locations = window.jobComparisonLocations;

  if (!locations) {
    locationMessage.textContent =
      'Vui lòng tính khoảng cách trước khi xem bản đồ.';
    return;
  }

  const { home, companyOne, companyTwo } = locations;

  $('#comparisonMap').hidden = false;

  // Nếu bản đồ đã tồn tại thì xóa để tạo lại
  if (comparisonMap) {
    comparisonMap.remove();
    comparisonMap = null;
  }

  comparisonMap = L.map('comparisonMap');

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(comparisonMap);

  const points = [
    {
      location: home,
      title: 'Nơi ở của bạn'
    },
    {
      location: companyOne,
      title: comparedJobs[0].company_name,
      subtitle: comparedJobs[0].location
    },
    {
      location: companyTwo,
      title: comparedJobs[1].company_name,
      subtitle: comparedJobs[1].location
    }
  ];

  const bounds = [];

  points.forEach(point => {
    const lat = point.location.latitude;
    const lng = point.location.longitude;

    const marker = L.marker([lat, lng]).addTo(comparisonMap);

    const note = point.location.approximate
      ? '<br><small>Vị trí ước tính theo khu vực</small>'
      : '';

    marker.bindPopup(
      `<strong>${esc(point.title)}</strong>` +
      (point.subtitle ? `<br>${esc(point.subtitle)}` : '') +
      note
    );

    bounds.push([lat, lng]);
  });

  comparisonMap.fitBounds(bounds, {
    padding: [40, 40],
    maxZoom: 13
  });

  // Đảm bảo bản đồ hiển thị đúng kích thước
  setTimeout(() => {
    comparisonMap.invalidateSize();
  }, 100);

  $('#showMapButton').textContent = 'Cập nhật bản đồ';
});


/* ===== INITIALIZE ===== */

$('#compareButton').addEventListener(
  'click',
  compareSelectedJobs
);

loadComparisonOptions();