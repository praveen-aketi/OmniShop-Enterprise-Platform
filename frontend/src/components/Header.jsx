import React from 'react';

const Header = ({ title }) => {
    return (
        <header className="top-header">
            <h2 className="page-title">{title}</h2>
            <div className="user-profile">
                <div className="avatar">AD</div>
                <span className="username">Admin User</span>
            </div>
        </header>
    );
};

export default Header;
