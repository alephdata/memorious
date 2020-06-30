function changeSchedule (event) {
  let val = event.target.value;
  let crawler = event.target.getAttribute('data-crawler')
  fetch(`/invoke/${crawler}/change-schedule`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({'schedule': val})
  });
}

[...document.querySelectorAll('.schedule')].forEach((item) => {
  item.addEventListener('change', changeSchedule);
});