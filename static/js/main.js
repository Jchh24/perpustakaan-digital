function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('active');
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('active');
  }
}

function openEditBookModal(book) {
  const form = document.getElementById('editBookForm');
  if (!form) return;
  form.action = '/admin/books/' + book.id + '/edit';
  document.getElementById('edit_title').value = book.title || '';
  document.getElementById('edit_author').value = book.author || '';
  document.getElementById('edit_publisher').value = book.publisher || '';
  document.getElementById('edit_isbn').value = book.isbn || '';
  document.getElementById('edit_publication_year').value = book.publication_year || '';
  document.getElementById('edit_location').value = book.location || '';
  document.getElementById('edit_stock').value = book.stock || 1;
  document.getElementById('edit_category_id').value = book.category_id || '';
  document.getElementById('edit_cover_image').value = book.cover_image || '';
  document.getElementById('edit_description').value = book.description || '';
  openModal('editBookModal');
}

window.addEventListener('click', function(event) {
  if (event.target.classList.contains('modal')) {
    event.target.classList.remove('active');
  }
});
