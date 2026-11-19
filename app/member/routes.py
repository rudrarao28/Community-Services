from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Reservation, Book, ActivityLog
from app.auth.decorators import active_member_required

member_bp = Blueprint('member', __name__)


@member_bp.route('/dashboard')
@login_required
@active_member_required
def dashboard():
    """
    Student Member Personal Dashboard.
    Summarizes currently borrowed books, due dates, overdue notices, and fines.
    """
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    today = date.today()

    # Active borrows
    active_borrows = current_user.transactions.filter(
        Transaction.status.in_(['issued', 'overdue'])
    ).order_by(Transaction.due_date.asc()).all()

    # Calculate active overdue warnings & fines
    overdue_borrows = []
    current_accrued_fine = 0.0
    for tx in active_borrows:
        fine = tx.calculate_current_fine()
        current_accrued_fine += fine
        if tx.due_date < today:
            overdue_borrows.append(tx)

    # Active pending reservations
    active_reservations = current_user.reservations.filter(
        Reservation.status.in_(['pending', 'notified'])
    ).order_by(Reservation.created_at.desc()).all()

    # Recent completed return transactions
    recent_returns = current_user.transactions.filter_by(status='returned').order_by(Transaction.return_date.desc()).limit(5).all()

    # Total historical fines paid/assessed
    total_paid_fines = current_user.total_fines_accrued()

    return render_template(
        'member/dashboard.html',
        active_borrows=active_borrows,
        overdue_borrows=overdue_borrows,
        current_accrued_fine=current_accrued_fine,
        active_reservations=active_reservations,
        recent_returns=recent_returns,
        total_paid_fines=total_paid_fines
    )


@member_bp.route('/history')
@login_required
@active_member_required
def borrow_history():
    """Complete loan history for the logged in student."""
    page = request.args.get('page', 1, type=int)
    txs_paginated = current_user.transactions.order_by(Transaction.id.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('member/history.html', transactions=txs_paginated)


@member_bp.route('/reservations')
@login_required
@active_member_required
def my_reservations():
    """List of all book reservations submitted by this student."""
    reservations_list = current_user.reservations.order_by(Reservation.created_at.desc()).all()
    return render_template('member/reservations.html', reservations=reservations_list)


@member_bp.route('/reservations/cancel/<int:res_id>', methods=['POST'])
@login_required
@active_member_required
def cancel_reservation(res_id):
    """Cancel a pending reservation."""
    res = Reservation.query.filter_by(id=res_id, user_id=current_user.id).first_or_404()
    if res.status in ['pending', 'notified']:
        res.status = 'cancelled'
        
        log = ActivityLog(
            user_id=current_user.id,
            action=f"Member {current_user.name} cancelled reservation for '{res.book.title}'"
        )
        db.session.add(log)
        db.session.commit()
        flash(f"Reservation for '{res.book.title}' has been cancelled.", 'info')

    return redirect(url_for('member.my_reservations'))
