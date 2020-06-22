const schedule = document.querySelector('#schedule');

schedule.addEventListener('change', (event) => {
  let val = event.target.value;
  let crawler = event.target.getAttribute('data-crawler')
  console.log(event.target);
  fetch(`/invoke/${crawler}/change-schedule`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({'schedule': val})
  });
});