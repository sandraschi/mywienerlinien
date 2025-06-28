# Ant Design (antd)

Ant Design is a comprehensive design system for enterprise-level products. It provides high-quality React components out of the box and is designed to help developers create beautiful, responsive web applications with a consistent design language.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Layout System](#layout-system)
- [Form Handling](#form-handling)
- [Data Display](#data-display)
- [Navigation](#navigation)
- [Feedback](#feedback)
- [Theming](#theming)
- [Internationalization](#internationalization)
- [Performance](#performance)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Installation

### Prerequisites
- Node.js 10.0.0 or later
- React 16.12.0 or later

### Using npm
```bash
npm install antd @ant-design/icons
```

### Using yarn
```bash
yarn add antd @ant-design/icons
```

### Importing Styles
Add the following to your main CSS/SCSS file:
```css
@import '~antd/dist/antd.css'; /* or '~antd/dist/antd.less' for less */

/* For dark theme */
@import '~antd/dist/antd.dark.css';
```

Or import styles directly in your JavaScript:
```javascript
import 'antd/dist/antd.css';
// or 'antd/dist/antd.dark.less' for dark theme
```

## Getting Started

### Basic Example
```jsx
import React from 'react';
import { Button, Card } from 'antd';
import { SmileOutlined } from '@ant-design/icons';

const App = () => (
  <div style={{ padding: '24px' }}>
    <Card title="Welcome to Ant Design">
      <Button type="primary" icon={<SmileOutlined />}>
        Hello World
      </Button>
    </Card>
  </div>
);

export default App;
```

### Using with Create React App
For projects created with Create React App, you can use `craco` to customize the configuration:

1. Install craco:
```bash
npm install @craco/craco --save-dev
```

2. Create a `craco.config.js` file:
```javascript
module.exports = {
  style: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer'),
      ],
    },
  },
};
```

3. Update `package.json` scripts:
```json
{
  "scripts": {
    "start": "craco start",
    "build": "craco build",
    "test": "craco test"
  }
}
```

## Core Concepts

### Design Principles
1. **Natural** - Intuitive and predictable
2. **Certain** - Clear and unambiguous
3. **Meaningful** - Focus on content
4. **Growing** - Dynamic and evolving

### Component Design
- **ConfigProvider** - Global configuration for components
- **Theme** - Customizable design tokens
- **Localization** - Built-in internationalization support
- **Accessibility** - WCAG 2.0 compliant components

## Layout System

### Basic Layout
```jsx
import { Layout, Menu, Breadcrumb } from 'antd';
import {
  UserOutlined,
  LaptopOutlined,
  NotificationOutlined,
} from '@ant-design/icons';

const { SubMenu } = Menu;
const { Header, Content, Sider } = Layout;

const AppLayout = () => (
  <Layout>
    <Header className="header">
      <div className="logo" />
      <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['2']}>
        <Menu.Item key="1">nav 1</Menu.Item>
        <Menu.Item key="2">nav 2</Menu.Item>
        <Menu.Item key="3">nav 3</Menu.Item>
      </Menu>
    </Header>
    <Layout>
      <Sider width={200} className="site-layout-background">
        <Menu
          mode="inline"
          defaultSelectedKeys={['1']}
          defaultOpenKeys={['sub1']}
          style={{ height: '100%', borderRight: 0 }}
        >
          <SubMenu key="sub1" icon={<UserOutlined />} title="subnav 1">
            <Menu.Item key="1">option1</Menu.Item>
            <Menu.Item key="2">option2</Menu.Item>
            <Menu.Item key="3">option3</Menu.Item>
            <Menu.Item key="4">option4</Menu.Item>
          </SubMenu>
          <SubMenu key="sub2" icon={<LaptopOutlined />} title="subnav 2">
            <Menu.Item key="5">option5</Menu.Item>
            <Menu.Item key="6">option6</Menu.Item>
            <Menu.Item key="7">option7</Menu.Item>
            <Menu.Item key="8">option8</Menu.Item>
          </SubMenu>
          <SubMenu
            key="sub3"
            icon={<NotificationOutlined />}
            title="subnav 3"
          >
            <Menu.Item key="9">option9</Menu.Item>
            <Menu.Item key="10">option10</Menu.Item>
            <Menu.Item key="11">option11</Menu.Item>
            <Menu.Item key="12">option12</Menu.Item>
          </SubMenu>
        </Menu>
      </Sider>
      <Layout style={{ padding: '0 24px 24px' }}>
        <Breadcrumb style={{ margin: '16px 0' }}>
          <Breadcrumb.Item>Home</Breadcrumb.Item>
          <Breadcrumb.Item>List</Breadcrumb.Item>
          <Breadcrumb.Item>App</Breadcrumb.Item>
        </Breadcrumb>
        <Content
          className="site-layout-background"
          style={{
            padding: 24,
            margin: 0,
            minHeight: 280,
          }}
        >
          Content
        </Content>
      </Layout>
    </Layout>
  </Layout>
);

export default AppLayout;
```

### Grid System
```jsx
import { Row, Col, Card } from 'antd';

const GridExample = () => (
  <div style={{ padding: '24px' }}>
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={8} lg={6} xl={4}>
        <Card>Column 1</Card>
      </Col>
      <Col xs={24} sm={12} md={8} lg={6} xl={4}>
        <Card>Column 2</Card>
      </Col>
      <Col xs={24} sm={12} md={8} lg={6} xl={4}>
        <Card>Column 3</Card>
      </Col>
      {/* More columns */}
    </Row>
  </div>
);
```

## Form Handling

### Basic Form
```jsx
import { Form, Input, Button, Checkbox } from 'antd';

const LoginForm = () => {
  const onFinish = (values) => {
    console.log('Success:', values);
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  return (
    <Form
      name="basic"
      labelCol={{ span: 8 }}
      wrapperCol={{ span: 16 }}
      initialValues={{ remember: true }}
      onFinish={onFinish}
      onFinishFailed={onFinishFailed}
      autoComplete="off"
    >
      <Form.Item
        label="Username"
        name="username"
        rules={[{ required: true, message: 'Please input your username!' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        label="Password"
        name="password"
        rules={[{ required: true, message: 'Please input your password!' }]}
      >
        <Input.Password />
      </Form.Item>

      <Form.Item name="remember" valuePropName="checked" wrapperCol={{ offset: 8, span: 16 }}>
        <Checkbox>Remember me</Checkbox>
      </Form.Item>

      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

### Dynamic Form Fields
```jsx
import { Form, Input, Button, Space } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';

const DynamicFields = () => {
  const onFinish = (values) => {
    console.log('Received values of form:', values);
  };

  return (
    <Form name="dynamic_form_nest_item" onFinish={onFinish} autoComplete="off">
      <Form.List name="users">
        {(fields, { add, remove }) => (
          <>
            {fields.map(({ key, name, fieldKey, ...restField }) => (
              <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                <Form.Item
                  {...restField}
                  name={[name, 'first']}
                  fieldKey={[fieldKey, 'first']}
                  rules={[{ required: true, message: 'Missing first name' }]}
                >
                  <Input placeholder="First Name" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'last']}
                  fieldKey={[fieldKey, 'last']}
                  rules={[{ required: true, message: 'Missing last name' }]}
                >
                  <Input placeholder="Last Name" />
                </Form.Item>
                <MinusCircleOutlined onClick={() => remove(name)} />
              </Space>
            ))}
            <Form.Item>
              <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                Add field
              </Button>
            </Form.Item>
          </>
        )}
      </Form.List>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};
```

## Data Display

### Table with Pagination
```jsx
import { Table, Tag, Space } from 'antd';

const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    render: (text) => <a>{text}</a>,
  },
  {
    title: 'Age',
    dataIndex: 'age',
    key: 'age',
  },
  {
    title: 'Address',
    dataIndex: 'address',
    key: 'address',
  },
  {
    title: 'Tags',
    key: 'tags',
    dataIndex: 'tags',
    render: (_, { tags }) => (
      <>
        {tags.map((tag) => {
          let color = tag.length > 5 ? 'geekblue' : 'green';
          if (tag === 'loser') {
            color = 'volcano';
          }
          return (
            <Tag color={color} key={tag}>
              {tag.toUpperCase()}
            </Tag>
          );
        })}
      </>
    ),
  },
  {
    title: 'Action',
    key: 'action',
    render: (_, record) => (
      <Space size="middle">
        <a>Invite {record.name}</a>
        <a>Delete</a>
      </Space>
    ),
  },
];

const data = [
  {
    key: '1',
    name: 'John Brown',
    age: 32,
    address: 'New York No. 1 Lake Park',
    tags: ['nice', 'developer'],
  },
  // More data...
];

const DataTable = () => (
  <Table 
    columns={columns} 
    dataSource={data} 
    pagination={{ pageSize: 5 }} 
  />
);
```

### Tabs
```jsx
import { Tabs } from 'antd';
import { AppleOutlined, AndroidOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;

const TabExample = () => (
  <Tabs defaultActiveKey="1">
    <TabPane
      tab={
        <span>
          <AppleOutlined />
          Tab 1
        </span>
      }
      key="1"
    >
      Content of Tab Pane 1
    </TabPane>
    <TabPane
      tab={
        <span>
          <AndroidOutlined />
          Tab 2
        </span>
      }
      key="2"
    >
      Content of Tab Pane 2
    </TabPane>
  </Tabs>
);
```

## Navigation

### Menu
```jsx
import { Menu } from 'antd';
import {
  AppstoreOutlined,
  MailOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { SubMenu } = Menu;

class NavigationMenu extends React.Component {
  state = {
    current: 'mail',
  };

  handleClick = (e) => {
    console.log('click ', e);
    this.setState({ current: e.key });
  };

  render() {
    const { current } = this.state;
    return (
      <Menu onClick={this.handleClick} selectedKeys={[current]} mode="horizontal">
        <Menu.Item key="mail" icon={<MailOutlined />}>
          Navigation One
        </Menu.Item>
        <Menu.Item key="app" disabled icon={<AppstoreOutlined />}>
          Navigation Two
        </Menu.Item>
        <SubMenu icon={<SettingOutlined />} title="Navigation Three - Submenu">
          <Menu.ItemGroup title="Item 1">
            <Menu.Item key="setting:1">Option 1</Menu.Item>
            <Menu.Item key="setting:2">Option 2</Menu.Item>
          </Menu.ItemGroup>
          <Menu.ItemGroup title="Item 2">
            <Menu.Item key="setting:3">Option 3</Menu.Item>
            <Menu.Item key="setting:4">Option 4</Menu.Item>
          </Menu.ItemGroup>
        </SubMenu>
        <Menu.Item key="alipay">
          <a href="https://ant.design" target="_blank" rel="noopener noreferrer">
            Navigation Four - Link
          </a>
        </Menu.Item>
      </Menu>
    );
  }
}
```

## Feedback

### Modal
```jsx
import { Button, Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';

const { confirm } = Modal;

const showConfirm = () => {
  confirm({
    title: 'Do you want to delete these items?',
    icon: <ExclamationCircleOutlined />,
    content: 'Some descriptions',
    onOk() {
      console.log('OK');
    },
    onCancel() {
      console.log('Cancel');
    },
  });
};

const ModalExample = () => (
  <Button type="primary" onClick={showConfirm}>
    Confirm
  </Button>
);
```

### Notification
```jsx
import { Button, notification } from 'antd';

const openNotification = () => {
  notification.open({
    message: 'Notification Title',
    description:
      'This is the content of the notification. This is the content of the notification. This is the content of the notification.',
    onClick: () => {
      console.log('Notification Clicked!');
    },
  });
};

const NotificationExample = () => (
  <Button type="primary" onClick={openNotification}>
    Open the notification box
  </Button>
);
```

## Theming

### Custom Theme
Create a `theme.js` file:
```javascript
module.exports = {
  'primary-color': '#1DA57A',
  'link-color': '#1DA57A',
  'border-radius-base': '2px',
  // More theme variables...
};
```

Then modify your webpack config:
```javascript
// webpack.config.js
const theme = require('./theme');

module.exports = {
  // ...
  module: {
    rules: [
      {
        test: /\.less$/,
        use: [
          // ...
          {
            loader: 'less-loader',
            options: {
              lessOptions: {
                modifyVars: theme,
                javascriptEnabled: true,
              },
            },
          },
        ],
      },
    ],
  },
};
```

### Dark Theme
```javascript
// In your main stylesheet
@import '~antd/dist/antd.dark.css';
```

## Internationalization

### Basic Setup
```jsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/lib/locale/zh_CN';
import moment from 'moment';
import 'moment/locale/zh-cn';

moment.locale('zh-cn');

const App = () => (
  <ConfigProvider locale={zhCN}>
    <YourApp />
  </ConfigProvider>
);
```

## Performance

### Code Splitting
```jsx
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

const App = () => (
  <Suspense fallback={<Spin />}>
    <HeavyComponent />
  </Suspense>
);
```

### Virtual List
For large lists, use `react-window` or `react-virtualized` with Ant Design components.

## Best Practices

1. **Component Size**
   - Use `size` prop consistently (small, middle, large)
   - Avoid inline styles for better performance

2. **Form Handling**
   - Use `Form.useForm()` hook for better performance
   - Leverage `initialValues` for controlled components

3. **Data Fetching**
   - Use `useEffect` with cleanup
   - Implement proper loading states

4. **Accessibility**
   - Always provide `alt` text for images
   - Use semantic HTML elements
   - Ensure keyboard navigation works

## Troubleshooting

### Common Issues

1. **Style Not Loading**
   - Ensure CSS/less is imported correctly
   - Check webpack configuration for style loaders

2. **Locale Not Working**
   - Make sure to import both `moment` locale and Ant Design locale
   - Verify `ConfigProvider` is properly set up

3. **Form Validation Issues**
   - Check field `name` props
   - Ensure `rules` are properly defined

## Resources

- [Official Documentation](https://ant.design/)
- [GitHub Repository](https://github.com/ant-design/ant-design/)
- [Ant Design Pro](https://pro.ant.design/)
- [Ant Design Components](https://ant.design/components/overview/)
- [Ant Design Icons](https://ant.design/components/icon/)
- [Ant Design Pro Components](https://procomponents.ant.design/)

## License

Ant Design is open source and licensed under the MIT License. See the [LICENSE](https://github.com/ant-design/ant-design/blob/master/LICENSE) file for more information.
