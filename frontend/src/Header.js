import styles from './Header.module.css';

function Header() {
    return (
        <header className={styles.header}>
            <h1>Now Playing</h1>
            <nav>
                <a href="https://blog.cha-king.com">Blog</a>
            </nav>
        </header>
    )
}


export default Header;
